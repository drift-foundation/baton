"""W285463 — the shared token-bound maintenance facility.

THE DEFECT THIS EXISTS TO REMOVE, confirmed by the parent's source research
(W275633) against this tree: every governed writer on the FIRST preparation
path is the HOST. `workspaces.assignment_workspace` creates the attempt home,
its entries and `workspace/result-<attempt>`, and adopts the configured group
on all of them, in the manager's own process -- and holds no resource token
while doing it. `custody.custody_act` does own a container lifecycle, and it
composes a FOREGROUND `run --rm` that no token admits, binds or settles.

So the resource a task will contend for is written by a party that holds no
permission to write it, and the existing uncertainty episode -- which is real
and is retained -- records that a SUBMITTED request may still land, not that a
container was correlated, admitted and proved gone.

WHAT THIS MODULE IS. One reusable scoped act: a maintenance execution that
holds a shared resource token over the SAME governed domain a task start
contends for, performs one manager-owned preparation verb INSIDE a container,
and is settled by the host on evidence rather than on output.

    acquire -> journal_launch -> create (inert) -> bind_container
            -> admit_activation -> start -> settle_activation
            -> wait -> logs -> validate -> prove cessation -> returned

FIVE PROPERTIES, and each one is a thing the current path cannot state:

ONE MOUNT, AND IT IS NEVER THE HOME. The attempt home holds `credentials`,
`credential-state` and `custody` beside `inputs` and `workspace`. A
preparation that mounted the home writable to create something under
`workspace` would silently authorize effects on all of them, so what is
mounted is the ONE derived root -- and the object being established is created
INSIDE it, by name, by the program. Absent rather than denied.

THE TOKEN IS THE HOLD. There is no second journal and no path-only lock: the
generation this act acquires is `tokens`' own, in the same control store, over
the same `workspace` resource kind and the same `device:inode` identity a task
start resolves. So a task cannot acquire while a preparation is outstanding,
and an interrupted preparation is exactly the `tokens.unresolved` cut G1
already reports.

A DISTINCT EXECUTION IDENTITY, AND NO FABRICATED TASK CLAIM. The execution
this token permits is the maintenance act, named as one; the attempt travels
as `acquire`'s optional ASSOCIATION, which writes no attempts row and mints no
claim.

THE HOST SETTLES, AND IT SETTLES THREE THINGS SEPARATELY. Whether the
preparation reported its own accountable outcome; whether THIS EXACT container
and any writer it left are positively gone; and whether the token may be
returned. An answer to the first is not an answer to the second, and neither
on its own returns the token.

AND AN UNKNOWN STAYS HELD. No document, an unreadable document, a document for
another submission, an unproved absence, an exit nobody can attribute -- every
one of them leaves the generation outstanding with its launch and container
correlated, which is the state an operator and `tokens.unresolved` can act on.
Nothing here reopens, resets or replaces on the strength of output, an exit
status, a stop order or an elapsed deadline.

WHAT IS PRESERVED RATHER THAN MOVED. Approver ruling 2026-08-30 (W43975) says
the result root is established BEFORE the runtime starts, that custody derives
that exact locator and never creates a missing one. This changes the WRITER and
not the ruling: the establishment still happens before any task start, and
`custody._derived_root`'s refusal of a missing result root at cleanup time is
untouched.
"""

import os
import stat

from ..contracts import ContractRefusal
from ..contracts.errors import name_value
from . import boundaries, custody, oci, tokens

__all__ = ["PREPARATIONS", "MAINTENANCE_ROOT", "MAINTENANCE_PROGRAM",
           "MaintenanceAnswer", "check_preparation", "prepare"]


# THE CLOSED VOCABULARY. One verb, and the set exists so that a second one is
# an addition to a vocabulary rather than a new operand: there is no command
# here, only a verb this module recognises.
#
# `establish-result-root` IS the real governed host writer on the first
# preparation path, which is why it is the selected one rather than a
# demonstration act -- the mutation it performs is the one
# `workspaces.assignment_workspace` performs on the host today.
ESTABLISH_RESULT_ROOT = "establish-result-root"
PREPARATIONS = (ESTABLISH_RESULT_ROOT,)

# WHAT EACH VERB ANSWERS, closed and typed -- the receiving half of the same
# rule `check_preparation` is the sending half of, and the same discipline
# `custody._CUSTODY_RESULT` carries: a zero exit plus an unrelated document is
# no stronger an account than a zero exit plus no document.
#
# `submission` is the token's OWNER, echoed. It is what makes one answer belong
# to one GENERATION rather than to any act over the same root.
MAINTENANCE_VERSION = 1
_PREPARED = {
    ESTABLISH_RESULT_ROOT: {"version": int, "submission": str, "place": str,
                            "established": bool, "mode": str,
                            "running_as": list},
}

# THE PROGRAM'S OWN TYPED REFUSAL, which is the other document it can print. It
# is accountable -- it says the act did not happen and why -- and it is never a
# successful account of the verb that was asked for.
_REFUSED = "refused"
_REFUSAL = {"version": int, "submission": str, "why": str}

# WHERE THE ONE MOUNT LANDS. Fixed rather than composed: a container path a
# caller could choose is an operand that decides what the program writes.
MAINTENANCE_ROOT = "/maintenance"

# A NAME A RESTARTED MANAGER CAN RE-DERIVE, for the reason `custody.CUSTODY_NAME`
# exists: a helper that outlives its act has to be findable by a manager that
# never saw it start. Derived, never chosen -- see `_maintenance_identity`.
MAINTENANCE_NAME = "baton-maintenance"

# THE GOVERNED RESOURCE KIND, AND IT IS THE TASK'S OWN. `tokens.Governance`
# composes `workspace` for a task start, so a maintenance act naming anything
# else would take a token that excludes nobody -- which is the "second token
# journal" this Work's finding refuses. One kind, one domain, one journal.
MAINTENANCE_KIND = "workspace"

# THE TIMERS, RECONCILED RATHER THAN RESTATED.
#
# `custody` already carries two numbers for the same shape and they are about a
# DIFFERENT act: `CUSTODY_SECONDS` is 1800 because a `discard` over a large
# worker tree is real work. A preparation is not: it creates one directory and
# fixes its mode.
#
# WHAT MATTERS IS THAT THE CLIENT TIMEOUT IS NOT THE GRANT. The grant is the
# token's lifetime and it is G1's own number; the program's alarm is how an
# overrun is ordinarily REPORTED; the act bound is the backstop for a call that
# never reaches the program at all. Ordered and summed:
#
#     PREPARE_SECONDS (300) < MAINTENANCE_ACT_SECONDS (360)
#     MAINTENANCE_ACT_SECONDS + RECLAIM_STOP_SECONDS (365) < 900
#
# so the whole act plus its reclamation is bounded strictly inside the grant,
# and an ordinary slow act is accounted for rather than lost.
#
# THE STOP GRACE IS THE ONE CUSTODY ACTUALLY SPENDS, and review
# 2026-09-27T13-42-58Z is right that the first cut advertised otherwise. It named
# `tokens.STOP_GRACE_SECONDS` (30) while every reclamation on this path goes
# through `custody._reclaimed`, which spends `CUSTODY_STOP_SECONDS` (5) and takes
# no timeout operand -- so the declared profile described a number this code never
# passed anywhere. What is declared now is what is spent; G1's 30 seconds belongs
# to a different act and is not this path's, and saying so is cheaper than making
# two numbers agree by widening custody's signature for no measured need.
MAINTENANCE_SECONDS = tokens.LIFETIME_SECONDS
PREPARE_SECONDS = 300
MAINTENANCE_ACT_SECONDS = PREPARE_SECONDS + 60
RECLAIM_STOP_SECONDS = custody.CUSTODY_STOP_SECONDS

# NO RENEWAL IS TAKEN HERE, and that is a selection rather than an omission.
# G1's `tokens.renew` exists and is available to a caller that needs it; a
# bounded preparation that cannot finish in 900 seconds is one to reconcile,
# because extending a grant is how an act that is not going to end stays
# permitted.
RENEWALS_TAKEN = 0

# THE MODE THE PREPARED OBJECT CARRIES. `02770` is what
# `workspaces.adopt_workspace_group` establishes on the writable root: group
# write, and setgid so what the worker creates inside stays in the configured
# group. Spelled here because the program is a constant of this module and must
# not read policy out of its environment.
PREPARED_MODE = 0o2770

# -- the durable maintenance window and its authoritative outcome -------------
#
# W285463 review 2026-09-27T13-17-14Z, R1 and R3, and one mechanism answers both
# because they are two halves of the same missing fact.
#
# R3: the token's RETURN is not an outcome. It says the resource is free; it does
# not say WHAT was prepared, whether the object validated, or which container
# answered for it -- so nothing durable recorded the settlement the child brief
# requires to be separate from the report and from the cessation.
#
# R1: the reciprocal exclusion could not be written the obvious way. A custody
# claim decides inside `BEGIN IMMEDIATE`, and the maintenance token's domain is
# `device:inode` of a root -- so asking "is a maintenance act holding this tree"
# through the token journal would mean an `lstat` UNDER THE WRITE LOCK, which is
# exactly the external I/O DB-2 forbids there.
#
# SO THE WINDOW IS RECORDED BY DERIVED IDENTITY, the same way
# `workspaces.standing_removal` is, and for the same reason it exists: a party
# that cannot compute the other party's identity can still read this one. It is
# NOT a second permission system -- the shared token remains the only thing that
# admits an effect on the resource, and this record admits nothing. What it
# carries is visibility and the outcome.
MAINTENANCE_OWNERSHIP_KIND = "workspace-maintenance.ownership"
MAINTENANCE_SETTLED_KIND = "workspace-maintenance.settled"
MAINTENANCE_ORPHAN_KIND = "workspace-maintenance.orphan"

# WHAT A SETTLEMENT MAY SAY IT IS, closed like every other document here.
#
#   prepared               the authoritative outcome: this exact container ran,
#                          its account validated member by member, and the object
#                          it established is inside the governed resource
#   refused-nothing-crossed  the act refused before any container existed, so the
#                          window closes having authorized nothing
#   orphan-proved-absent   a container was created and the act then refused; the
#                          exact runtime was ended and PROVED gone, so no effect
#                          can still arrive and the window closes
#
# ANY OTHER ENDING LEAVES THE WINDOW OPEN, which is the honest state: an outcome
# nobody established is not a settlement, and custody, allocation and the next
# maintenance act are excluded until an operator reconciles it.
SETTLED_PREPARED = "prepared"
SETTLED_REFUSED = "refused-nothing-crossed"
SETTLED_ORPHANED = "orphan-proved-absent"
DISPOSITIONS = (SETTLED_PREPARED, SETTLED_REFUSED, SETTLED_ORPHANED)

# W285463 review 2026-09-27T14-27-04Z: THE FAILED EXECUTION IS RECORDED WITHOUT
# DISCHARGING ANYTHING, and that correction is the reviewer's rather than mine.
#
# My previous cut made a nonzero exit a SETTLEMENT (`execution-failed`), which closed
# the window and returned the token -- on the argument that a known exit with a proved
# cessation is not an uncertainty. The review is right that this conflates three
# separate facts (TOK-8): cessation is known, the EXIT is known, and what the
# execution DID to the resource is not. A failed container may have left partial
# output that needs repair (TOK-12), so freeing the resource lets an ordinary
# replacement take a tree nobody has established the state of.
#
# SO THIS KIND RECORDS THE FAILURE AND CLOSES NOTHING. The window keeps standing and
# the token keeps the resource held, which is the conservative outcome the review
# names as acceptable; a settled resource state is reached only through the positive
# exit-0 proof -- an accountable, submission-matching, semantically matching report
# whose object is confirmed inside the governed resource -- and never inferred from an
# exit code.
MAINTENANCE_FAILED_KIND = "workspace-maintenance.failed"

# This manager's bound on maintenance windows over one root, and the same
# fail-closed rule `custody._MOST_HOLDS` states: a root that has accumulated this
# many is one to reconcile rather than one to add to.
_MOST_ACTS = 64


def _act_identity(kind, assignment_id, which, ordinal):
    """One identity per (attempt, root, ORDINAL), never reused.

    The ordinal is IN the identity for `custody._hold_identity`'s reason: two
    maintenance acts over one root are two facts, and a settlement written for
    the first must not close the second.
    """
    from ..contracts.canonical import digest

    return kind + ":" + digest({"attempt_id": assignment_id, "root": which,
                                "ordinal": ordinal})[len("sha256:"):]


def standing_maintenance(control, assignment_id, which):
    """Every maintenance window over this root that carries NO settlement.

    READ BY DERIVED IDENTITY rather than by scanning the journal table, which is
    this build's rule for operation records -- `workspaces.standing_removal`
    states it, and it is what makes this readable from inside another act's write
    transaction with no filesystem work at all.

    A WINDOW WITH NO SETTLEMENT IS STANDING, whatever became of the manager that
    opened it. Nothing here guesses that a vanished act finished.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    custody.check_custody_root(which)
    standing = []
    ordinal = 1
    while ordinal <= _MOST_ACTS:
        found = control.operation_record(
            _act_identity(MAINTENANCE_OWNERSHIP_KIND, assignment_id, which,
                          ordinal))
        if found is None:
            return standing
        if control.operation_record(
                _act_identity(MAINTENANCE_SETTLED_KIND, assignment_id, which,
                              ordinal)) is None:
            standing.append((ordinal, found))
        ordinal += 1
    return standing


def _window(control, assignment_id, which, ordinal, kind):
    """One recorded document of this kind for this window, or `None`."""
    record = control.operation_record(
        _act_identity(kind, assignment_id, which, ordinal))
    if record is None or record["state"] != "committed":
        return None
    import json as _json

    result = record["result"]
    return _json.loads(result) if type(result) is str else result


def maintenance_settlement(control, assignment_id, which, ordinal=None):
    """THE AUTHORITATIVE OUTCOME, read back from the journal.

    R3's fresh-handle half: a manager that holds no answer object -- a later
    process, a different store handle -- asks this and is told what was prepared,
    under which token generation, by which container, and on what evidence.
    Without an `ordinal` it answers the latest recorded window's settlement.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    custody.check_custody_root(which)
    if ordinal is not None:
        return _window(control, assignment_id, which, ordinal,
                       MAINTENANCE_SETTLED_KIND)
    found = None
    for one in range(1, _MOST_ACTS + 1):
        if control.operation_record(
                _act_identity(MAINTENANCE_OWNERSHIP_KIND, assignment_id, which,
                              one)) is None:
            break
        settled = _window(control, assignment_id, which, one,
                          MAINTENANCE_SETTLED_KIND)
        if settled is not None:
            found = settled
    return found


def maintenance_failure(control, assignment_id, which, ordinal):
    """The recorded failure of an execution that ran and exited nonzero.

    A FACT AND NOT A DISCHARGE. Reading one says the container ran, ended, and
    exited with this status, and whether its report could be accounted for; it says
    nothing about the state of the resource, which is why the window it belongs to
    is still standing when this exists.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    custody.check_custody_root(which)
    return _window(control, assignment_id, which, ordinal,
                   MAINTENANCE_FAILED_KIND)


def maintenance_orphan(control, assignment_id, which, ordinal):
    """The exact runtime a refused act created and could not prove gone."""
    boundaries.identity(assignment_id, "an assignment identity")
    custody.check_custody_root(which)
    return _window(control, assignment_id, which, ordinal,
                   MAINTENANCE_ORPHAN_KIND)


def _container_exit(waited):
    """THE CONTAINER'S OWN EXIT CODE, from a successful wait, or `(None, why)`.

    W285463 review 2026-09-27T14-07-07Z, and it is a confirmed false success of
    mine rather than a hardening. `docker wait` answers TWO different things and I
    was reading one of them: the CLI status says whether the manager's command
    worked, and the STDOUT is the exit code of the container it waited for. My
    earlier cut ignored the stdout entirely and then used the LOGS command's CLI
    status as the act's status -- so a container that exited 17 was reported `ok`,
    settled as `prepared` and its token returned, because two engine commands about
    it had succeeded. A correct report and a real filesystem effect do not turn a
    failed execution into a successful one.

    TRANSPORT AND OUTCOME ARE DIFFERENT FACTS, and this is where they are told
    apart. A non-zero CLI status is handled by the caller as an unknown -- nobody
    learned whether the container ended. A SUCCESSFUL call whose answer this reader
    cannot parse is also an unknown: missing, multiple, non-numeric or out of the
    range a process exit can occupy. Only one exact whole number in 0..255 is an
    outcome, and it is the outcome of THIS container because the wait named it.
    """
    lines = [one.strip() for one in (waited.get("stdout") or "").splitlines()
             if one.strip()]
    if len(lines) != 1:
        return None, (f"the engine answered {len(lines)} exit codes for one "
                      f"container, and a wait that does not report exactly one "
                      f"outcome has not told this manager what happened")
    found = lines[0]
    if not found.isdigit():
        return None, (f"the engine reported exit {name_value(found)}, which is "
                      f"not a whole number; a status this manager cannot read is "
                      f"not one it acts on")
    value = int(found)
    if not 0 <= value <= 255:
        return None, (f"the engine reported exit {value}, which is outside the "
                      f"range a process exit occupies; this manager does not "
                      f"interpret it")
    return value, None


def _conflicting(control, assignment_id, which):
    """WHY these roots are not free right now, as one sentence, or `None`.

    W285463 review 2026-09-27T13-56-09Z, and the reason this is ONE function is
    that my previous cut had two: the window admission and the token eligibility
    each read custody overlap and standing removals, and NEITHER read a standing
    allocation. So the reviewer committed a real `_admitted_allocation`, proved it
    standing, and this facility went on to run a preparation inside roots another
    act was in the middle of creating. One reader means the two decisions cannot
    ask different questions again.

    EVERY ACT THAT HOLDS THESE ROOTS IN FLIGHT, by the owner's own reader:

        custody uncertainty     custody._standing_overlap   both roots
        allocation in flight    workspaces.standing_allocation
        removal in flight       workspaces.standing_removal
        cleanup in flight       workspaces.standing_cleanup
        adoption in flight      workspaces.standing_adoption

    JOURNAL READS ONLY, which is what lets this run inside `BEGIN IMMEDIATE` and
    inside `tokens.acquire`'s eligibility predicate: every one of these is a walk
    over derived operation identities, and not one of them touches a filesystem or
    an engine. That restriction is why the maintenance side reads the WINDOW rather
    than the token, and it is the same restriction here.

    ONE ATTEMPT ONLY. These readers are all per-attempt, so two different attempts
    say nothing about each other and this serializes nothing across them.
    """
    from . import workspaces

    standing = custody._standing_overlap(control, assignment_id, which)
    if standing is not None:
        return (f"attempt {name_value(assignment_id)}'s "
                f"{standing['held']['root']} root carries unreconciled uncertainty "
                f"episode {standing['episode']!r}, whose helper is "
                f"{name_value(standing['held']['helper_identity'])}; a governed "
                f"preparation is not performed inside a tree an earlier act may "
                f"still be writing")
    for what, standing in (
            ("allocation", workspaces.standing_allocation(control,
                                                          assignment_id)),
            ("removal", workspaces.standing_removal(control, assignment_id)),
            ("cleanup", workspaces.standing_cleanup(control, assignment_id)),
            ("adoption", workspaces.standing_adoption(control, assignment_id))):
        if standing:
            ordinal, _record = standing[0]
            return (f"{what} {ordinal} of attempt "
                    f"{name_value(assignment_id)}'s roots was admitted and has "
                    f"recorded no completion, so another act is mid-flight over "
                    f"them; a governed preparation is a WRITER inside these roots "
                    f"and is not admitted beside one")
    return None


def _admitted(control, assignment_id, which, *, operation, name, domain,
              pre_allocation):
    """Open ONE maintenance window over this root, atomically, or refuse.

    R1. THE DECISION IS THE READ THAT HAPPENS UNDER THE WRITE LOCK, which is the
    correction rather than a detail: the earlier cut checked
    `custody._standing_overlap` outside every transaction and then acquired a
    token with no condition attached, so a custody hold that committed in between
    was invisible -- the reviewer's probe interposed exactly there and the
    preparation wrote anyway.

    `BEGIN IMMEDIATE` and JOURNAL READS ONLY. Custody overlap, standing removals
    and prior maintenance windows are all read by derived identity, so this
    transaction touches no filesystem and no engine.

    NO STANDING WINDOW IS EVER ADOPTED, and that is review 2026-09-27T13-42-58Z's
    correction rather than my first shape. I had a same-act replay adopt its own
    ordinal -- matching verb, domain and derived container identity -- which the
    reviewer was right to refuse: two live executors of one operation match on all
    three, so the second would have adopted the first's window and could then CLOSE
    it on its own refusal, clearing a shared exclusion somebody else was relying on.

    AND THERE IS NOTHING LEGITIMATE THAT ADOPTION BUYS. Every way a window is left
    standing is an UNKNOWN by construction: an orphan whose absence could not be
    proved, an outcome nobody could account for, or a manager that died mid-act.
    Each of those is a state to reconcile, not one to continue from -- and the
    restart case is W285465's scope. So a standing window refuses, naming its root,
    its ordinal, its verb, its container and the incarnation that opened it, which
    is what an operator or a recovery pass needs.

    BOTH ROOTS ARE READ. `custody._derived_root` puts the result root INSIDE the
    workspace, so a window over either covers material the other contains -- the
    same rule `_standing_overlap` and `_journal_holds` already apply, now applied to
    this act's own admission as the review asked.
    """
    from . import workspaces
    from .store import _recorded, manager_signature

    connection = control._connection
    connection.execute("BEGIN IMMEDIATE")
    try:
        conflict = _conflicting(control, assignment_id, which)
        if conflict is not None:
            raise ContractRefusal("refused", "precondition", conflict)
        for root in custody.CUSTODY_ROOTS:
            for ordinal, record in standing_maintenance(control, assignment_id,
                                                        root):
                import json as _json

                held = record["result"]
                held = _json.loads(held) if type(held) is str else (held or {})
                raise ContractRefusal(
                    "refused", "precondition",
                    f"attempt {name_value(assignment_id)}'s {root} root carries "
                    f"unsettled maintenance window {ordinal} for "
                    f"{name_value(held.get('verb'))} over "
                    f"{name_value(held.get('domain'))}, whose container is "
                    f"{name_value(held.get('helper_identity'))} and which was "
                    f"opened by incarnation "
                    f"{name_value(held.get('incarnation'))}; one maintenance act "
                    f"holds these overlapping roots at a time, and a window left "
                    f"standing is an unknown to reconcile rather than one to "
                    f"continue from or clear on somebody else's behalf")
        opened = 1
        while control.operation_record(
                _act_identity(MAINTENANCE_OWNERSHIP_KIND, assignment_id, which,
                              opened)) is not None:
            opened += 1
            if opened > _MOST_ACTS:
                raise ContractRefusal(
                    "integrity", "limit",
                    f"attempt {name_value(assignment_id)}'s {which} root has "
                    f"{_MOST_ACTS} recorded maintenance windows, which is this "
                    f"manager's bound; it is reconciled rather than acted on "
                    f"again")
        # THE EXECUTOR THAT OPENED IT, recorded so an operator or a recovery pass
        # can attribute a standing window to an incarnation rather than guess.
        # Nothing ADOPTS on the strength of it -- see the docstring -- and that is
        # the point: it is evidence, not authority.
        document = {"version": MAINTENANCE_VERSION,
                    "attempt_id": assignment_id, "root": which,
                    "ordinal": opened, "verb": operation, "domain": domain,
                    "pre_allocation": pre_allocation,
                    "incarnation": str(getattr(control, "incarnation", "")),
                    "helper_identity": name}
        control._record(
            _act_identity(MAINTENANCE_OWNERSHIP_KIND, assignment_id, which,
                          opened),
            MAINTENANCE_OWNERSHIP_KIND,
            manager_signature(MAINTENANCE_OWNERSHIP_KIND, document),
            "committed", _recorded(document), None)
        connection.execute("COMMIT")
    except BaseException:
        try:
            connection.execute("ROLLBACK")
        except Exception:
            pass
        raise
    return opened


def _eligible(control, assignment_id, which):
    """The PURE-DATABASE condition the acquisition itself is taken under.

    R1's second half, and it is deliberately the same three reads `_admitted`
    performs: the window admission and the token acquisition are two
    transactions, so a hold that commits between them must be refused by the
    SECOND one as well. `tokens.acquire` calls this inside its own
    `BEGIN IMMEDIATE`, which is why it may touch nothing but the journal -- the
    restriction DB-2 names, and the reason a directory check could never be the
    predicate here.
    """
    def asking(_connection):
        conflict = _conflicting(control, assignment_id, which)
        if conflict is None:
            return None
        return (f"{conflict}; a governed preparation is not ADMITTED over roots "
                f"another act is mid-flight over, and this condition is decided "
                f"inside the acquisition's own transaction")

    return asking


def _settled(control, assignment_id, which, ordinal, document):
    """Close ONE window with its outcome, durably, before the token is returned.

    R3. THE HOST'S OWN SETTLEMENT, and it is a record rather than a return value:
    the token return says the resource is free, and what this says is what
    happened -- the verb, the generation and owner, the exact container, the
    prepared object and its identity inside the governed resource, and the
    evidence the host validated. A later process asks
    `maintenance_settlement` and is told; nothing has to still hold an answer
    object.
    """
    from .store import manager_signature

    body = dict(document, version=MAINTENANCE_VERSION,
                attempt_id=assignment_id, root=which, ordinal=ordinal)
    if body["disposition"] not in DISPOSITIONS:      # pragma: no cover
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(body['disposition'])} is not a maintenance "
            f"disposition; the three this manager records are "
            f"{', '.join(DISPOSITIONS)}")
    return control.transact(
        _act_identity(MAINTENANCE_SETTLED_KIND, assignment_id, which, ordinal),
        MAINTENANCE_SETTLED_KIND,
        manager_signature(MAINTENANCE_SETTLED_KIND, body),
        lambda _connection: dict(body))


def _failed(control, assignment_id, which, ordinal, body):
    """Record WHAT HAPPENED to a failed execution, and discharge nothing."""
    from .store import manager_signature

    document = dict(body, version=MAINTENANCE_VERSION,
                    attempt_id=assignment_id, root=which, ordinal=ordinal)
    return control.transact(
        _act_identity(MAINTENANCE_FAILED_KIND, assignment_id, which, ordinal),
        MAINTENANCE_FAILED_KIND,
        manager_signature(MAINTENANCE_FAILED_KIND, document),
        lambda _connection: dict(document))


def _orphaned(control, assignment_id, which, ordinal, body):
    """Record the exact runtime a refused act created, and what is known of it.

    R2. A refusal that has already created a container owes an operator the
    container's identity and the truth about whether its absence was PROVED --
    `custody`'s own lesson that an acknowledgement is not an absence, written
    down rather than reported once into a diagnostic nobody kept.
    """
    from .store import manager_signature

    document = dict(body, version=MAINTENANCE_VERSION,
                    attempt_id=assignment_id, root=which, ordinal=ordinal)
    return control.transact(
        _act_identity(MAINTENANCE_ORPHAN_KIND, assignment_id, which, ordinal),
        MAINTENANCE_ORPHAN_KIND,
        manager_signature(MAINTENANCE_ORPHAN_KIND, document),
        lambda _connection: dict(document))


_PROGRAM_SOURCE = r'''
import json
import os
import signal
import stat
import sys

ROOT = "/maintenance"
VERBS = ("establish-result-root",)
MODE = 0o2770
SECONDS = __SECONDS__
VERSION = __VERSION__


def answered(document):
    sys.stdout.write(json.dumps(document, sort_keys=True) + "\n")
    sys.stdout.flush()


def refuse(why, code):
    """THE PROGRAM'S OWN ACCOUNT OF NOT ACTING, which is still an account."""
    answered({"maintenance": "refused", "version": VERSION,
              "submission": SUBMISSION, "why": why})
    raise SystemExit(code)


def expired(number, frame):
    refuse("the preparation did not finish within %d seconds and this program "
           "ended itself rather than holding the resource open" % SECONDS, 3)


VERB = sys.argv[1] if len(sys.argv) > 1 else ""
SUBMISSION = sys.argv[2] if len(sys.argv) > 2 else ""
PLACE = sys.argv[3] if len(sys.argv) > 3 else ""

signal.signal(signal.SIGALRM, expired)
signal.alarm(SECONDS)

if VERB not in VERBS:
    refuse("this program performs %s and was asked for %r" % (VERBS, VERB), 4)
# THE NAME IS A NAME. The host derives it and the program refuses anything that
# could leave the mounted root -- a separator, a traversal, an absolute path --
# because a program that resolved a compound name would be the second place the
# containment rule lives, and two places agree until they do not.
if not PLACE or PLACE in (os.curdir, os.pardir) or os.sep in PLACE \
        or (os.altsep and os.altsep in PLACE):
    refuse("%r is not a name this program establishes inside its own root"
           % PLACE, 4)

place = os.path.join(ROOT, PLACE)

established = False
try:
    held = os.lstat(place)
except FileNotFoundError:
    held = None
if held is None:
    # THE EFFECT, and it happens HERE -- inside the execution the token admits,
    # as the identity that owns what it creates.
    os.mkdir(place)
    established = True
elif stat.S_ISLNK(held.st_mode) or not stat.S_ISDIR(held.st_mode):
    # NOT REPAIRED AND NOT REPLACED. An entry at this name that is not its own
    # directory is state somebody else established, and removing it here would
    # be this program deciding something the host did not ask it to decide.
    refuse("%r already exists and is not its own directory; a preparation "
           "establishes and never replaces" % PLACE, 5)
# ESTABLISHED, NOT REQUESTED: `mkdir`'s mode is filtered through the umask and
# `chmod` on an existing directory is exact. Applied on the reopened path
# whether this act created it or found it, so the answer describes what IS.
os.chmod(place, MODE)
final = os.lstat(place)
answered({"maintenance": VERB, "version": VERSION, "submission": SUBMISSION,
          "place": PLACE, "established": established,
          "mode": oct(stat.S_IMODE(final.st_mode)),
          "running_as": [os.getuid(), os.getgid()]})
'''

# W285463 review R3: THE VERSION IS IN THE DOCUMENT, not only in the pin. The
# first cut called the schema "version 1" and printed no version field, which is
# a claim the representation could not answer for -- so a later build could not
# tell one representation from another and the receipt would record a number
# nothing had validated. It is substituted from this module's own constant, like
# the alarm, so the program and the validator cannot disagree.
MAINTENANCE_PROGRAM = _PROGRAM_SOURCE.replace(
    "__SECONDS__", str(PREPARE_SECONDS)).replace(
    "__VERSION__", str(MAINTENANCE_VERSION))


def check_preparation(operation):
    """One verb from the closed vocabulary, or a refusal.

    The same shape `custody.check_custody_operation` has, and for the same
    reason: a verb SELECTS among programs this module owns, so a value that is
    not one of them selects nothing at all.
    """
    boundaries.text(operation, "a maintenance preparation")
    if operation not in PREPARATIONS:
        raise ContractRefusal(
            "integrity", "schema",
            f"{name_value(operation)} is not a maintenance preparation; the "
            f"vocabulary this manager owns is {', '.join(PREPARATIONS)}, and a "
            f"preparation is chosen from it rather than described by its caller")
    return operation


def _maintenance_identity(store_place, assignment_id, which, operation):
    """The ONE name this act's container can have, DERIVED and never chosen.

    `custody._custody_identity`'s rule, applied to this family: the configured
    STORE is in the digest so the identity is unique to a deployment rather
    than to an attempt name, the attempt/root/verb are in it because those are
    what make one act different from another over the same tree, and the
    store's INCARNATION is deliberately not, because a restarted manager must
    be able to re-derive the name of the container it is reconciling.
    """
    from ..contracts.canonical import digest

    found = (MAINTENANCE_NAME + "-"
             + digest({"store": store_place, "assignment_id": assignment_id,
                       "which": which, "operation": operation})
             [len("sha256:"):][:custody._IDENTITY_HEX])
    if not custody._NAME.fullmatch(found):
        # UNREACHABLE BY CONSTRUCTION and asserted anyway: this is the one
        # place this family's names are made.
        raise ContractRefusal(
            "integrity", "schema",
            f"the derived maintenance identity {name_value(found)} is not a "
            f"name this build composes")
    return found


def _prepared_name(assignment_id):
    """The object `establish-result-root` establishes, as a NAME.

    The manager-derived result locator of ruling 2026-08-30 (W43975), spelled
    relative to the mounted root. It is composed from the attempt identity the
    store already validated and is never a caller operand, so the name the host
    validates afterwards and the name the program is given are one derivation.
    """
    boundaries.identity(assignment_id, "an assignment identity")
    return f"result-{assignment_id}"


def _execution_identity(assignment_id, which):
    """WHO this token permits to act, and it is not the task.

    A maintenance execution is a different actor from the assignment's runtime:
    `tokens.acquire` records the execution permitted to act, and recording the
    attempt's `runtime_attempt_id` here would be this module claiming to BE the
    task's execution -- which is the fabricated claim this Work's finding
    refuses. The attempt travels as the token's optional association instead.
    """
    return f"maintenance-execution:{assignment_id}:{which}"


def _operation_identity(operation, assignment_id, which):
    """WHICH act this is, stable across retries.

    `tokens.acquire` replays an operation that returns with identical operands,
    so this identity is what makes a retried preparation resume its OWN
    generation rather than allocate a second one over the same resource. The
    launch is journalled under this same identity, which is `Governance.reserve`'s
    own discipline: the launch a token names is the journalled start rather than
    a second act beside it.
    """
    return f"maintenance-{operation}:{assignment_id}:{which}"


def _resource_identity(place, name):
    """The PRE-ALLOCATION identity of the object this act establishes.

    `<device>:<inode>/<name>`, and both halves are load-bearing:

      * `<device>:<inode>` is the CONTAINING object, which is exactly
        `tokens.workspace_identity`'s answer for an attempt whose pinned
        workspace is this root. So the domain a preparation contends for is the
        domain a task start contends for -- the G1 conflict identity, retained
        rather than replaced.
      * `/<name>` names the object that does NOT EXIST YET. It is stable before
        the establishment and derivable after it, which is what a pre-allocation
        identity has to be, and it is the mapping the host validates afterwards
        by requiring the established object's parent to be that same
        `device:inode`.

    A path is NOT an identity here: the device and inode come from an `lstat`
    of the root this act re-opened from durable state, so nothing a caller holds
    selects it.
    """
    held = os.lstat(place)
    if not stat.S_ISDIR(held.st_mode) or stat.S_ISLNK(held.st_mode):
        raise ContractRefusal(
            "policy", "denied",
            f"{name_value(place)} is not a directory this manager allocated, "
            f"so the resource a preparation would contend for cannot be named")
    return f"{held.st_dev}:{held.st_ino}", f"{held.st_dev}:{held.st_ino}/{name}"


class MaintenanceAnswer:
    """WHAT ONE PREPARATION ANSWERED, and deliberately not a capability.

    `custody.CustodyAnswer`'s rule: no host path and no command vector crosses
    back, so nothing a caller holds afterwards selects a directory or runs
    anything. What it carries is the verb, the generation and container this act
    was correlated to, the engine's exit status, the accounted document, whether
    the token was RETURNED, and a bounded diagnostic.

    `held` IS THE HONEST HALF. A preparation whose outcome or cessation this
    manager could not establish answers `held=True` with the generation and
    container named, which is what an operator and `tokens.unresolved` need --
    rather than an exception that leaves the reader guessing which resource is
    outstanding.
    """

    __slots__ = ("_operation", "_generation", "_container", "_status",
                 "_answer", "_rendered", "_unaccounted", "_returned",
                 "_diagnostic")

    def __setattr__(self, name, value):
        raise ContractRefusal(
            "policy", "denied",
            f"a maintenance answer is what one act answered and is not "
            f"revised by its holder; {name_value(name)} stands as recorded")

    def __delattr__(self, name):
        self.__setattr__(name, None)

    @property
    def operation(self):
        return self._operation

    @property
    def generation(self):
        return self._generation

    @property
    def container(self):
        return self._container

    @property
    def status(self):
        return self._status

    @property
    def answer(self):
        return self._answer

    @property
    def rendered(self):
        return self._rendered

    @property
    def unaccounted(self):
        return self._unaccounted

    @property
    def returned(self):
        return self._returned

    @property
    def held(self):
        return not self._returned

    @property
    def diagnostic(self):
        return self._diagnostic

    @property
    def ok(self):
        """The act happened, said what it did, said THIS -- and is settled.

        `custody`'s three conditions plus the two this facility adds: a
        preparation whose token is still outstanding is not a completed
        preparation however good its document looked, and neither is one whose
        CONTAINER exited nonzero. Review 2026-09-27T14-07-07Z reached exactly that
        -- exit 17 with a correct report and a real effect, reported `ok` because
        the manager's own commands had succeeded.
        """
        return (self._answer is not None and self._unaccounted is None
                and self._returned and self._status == 0)


def _accountable(operation, document):
    """The document this act may be accounted for by, and why not if not.

    `custody._accountable`'s rule rather than a second one: held to a CLOSED
    member set, because a document with an unexpected member is a document from
    a program this module does not ship, and reading the recognised parts out of
    it is how a manager accounts for an act it did not understand.
    """
    if document is None:
        return None, "the act printed no document this manager could read"
    verb = document.get("maintenance")
    if verb == _REFUSED:
        shape, what = _REFUSAL, "a maintenance refusal"
    elif verb == operation:
        shape, what = _PREPARED[operation], f"a {operation} result"
    else:
        return None, (
            f"the act answered for {name_value(verb)} and this manager asked "
            f"for {name_value(operation)}; an account of a different act is "
            f"not an account of this one")
    missing = sorted(one for one in shape if one not in document)
    extra = sorted(one for one in document
                   if one != "maintenance" and one not in shape)
    if missing or extra:
        return None, (
            f"the act's document is not {what}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    for one, expected in shape.items():
        if type(document[one]) is not expected:
            return None, (
                f"the act's {name_value(one)} is not the {expected.__name__} "
                f"{what} answers")
    if verb != _REFUSED and (len(document["running_as"]) != 2
                             or any(type(one) is not int
                                    for one in document["running_as"])):
        return None, ("the act did not say which identity it ran as, and a "
                      "preparation whose execution identity is unstated is one "
                      "this manager cannot attribute")
    return document, None


def _answered(operation, generation, container, status, document, *,
              returned, diagnostic):
    """Mint the one answer for one act. Private, and the only minter."""
    import json

    accounted, why = _accountable(operation, document)
    made = object.__new__(MaintenanceAnswer)
    object.__setattr__(made, "_operation", operation)
    object.__setattr__(made, "_generation", generation)
    object.__setattr__(made, "_container", container)
    object.__setattr__(made, "_status", status)
    object.__setattr__(made, "_answer",
                       None if accounted is None else custody._frozen(accounted))
    object.__setattr__(made, "_rendered",
                       None if accounted is None
                       else json.dumps(accounted, sort_keys=True))
    object.__setattr__(made, "_unaccounted", why)
    object.__setattr__(made, "_returned", bool(returned))
    object.__setattr__(made, "_diagnostic", diagnostic)
    return made


def _document(stdout):
    """The LAST JSON object the container printed, or `None`.

    `custody._custodian_document`'s rule, and it is reused rather than
    restated: what a program prints before its answer is diagnostic, and the
    answer is the document -- so a reader that parsed the first line would be
    reading whatever an engine prefixed.
    """
    return custody._custodian_document(stdout)


def _create_vector(engine, *, image_digest, source, gid, name, operation,
                   submission, place):
    """The INERT container this act will later start, restrictions and all.

    PRIVATE, and `custody._custody_vector`'s round-ten reason is why: a
    composed argv carrying an authenticated bind source, returned to a caller,
    is a capability in somebody else's hands. It is composed and consumed
    inside `prepare`.

    `ACTIVATE_DEFERRED` RATHER THAN A RUN, which is the whole two-act shape:
    what this composes decides everything about the container and RUNS nothing,
    so the token can bind the identity that now exists and admit its activation
    before any process touches the resource.

    NOT `oci.run_vector`, for `custody`'s reason: a runtime is given inputs, a
    launch document and credentials and is expected to run somebody's
    assignment. This is given one directory and a verb, and sharing a composer
    would make every restriction here one an execution vector could relax.
    """
    from . import workspaces

    engine = oci._engine(engine)
    boundaries.text(image_digest, "an image digest")
    if not oci._IMAGE.match(image_digest):
        oci._refuse(f"{name_value(image_digest)} is not a sha256 image digest; "
                    f"a maintenance act runs the image this manager can name "
                    f"exactly", code="digest")
    # THE SAME EXECUTION IDENTITY THE CUSTODIAN RUNS AS, minted from the gid
    # this act read out of the store. W194457's mechanism: the writer owns what
    # it creates, so what it establishes is owned by the identity the worker
    # will run as -- and `identity_for` derives the uid itself, so there is no
    # integer here a caller chose.
    identity = workspaces.identity_for(
        workspaces.WorkspaceGroup(gid, workspaces._MINT))
    argv = [engine, *oci.ACTIVATIONS[oci.ACTIVATE_DEFERRED], "--name", name]
    for flag, value in custody._CUSTODY_RESTRICTIONS:
        argv.append(flag)
        if flag == "--user":
            value = workspaces.declared_identity_mapping(
                identity, f"{identity.uid}:{identity.gid}")
        if value is not None:
            argv.append(value)
    argv += ["--group-add", str(gid)]
    # THE ONE MOUNT, AND IT IS THE DERIVED ROOT RATHER THAN ITS PARENT. The
    # object this act establishes is created INSIDE it by name, so the home and
    # its credential siblings are not mounted at all -- absent rather than
    # denied, which survives a bug in the program this runs.
    argv += ["--mount",
             f"type=bind,source={source},target={MAINTENANCE_ROOT},"
             f"readonly=false"]
    argv += ["--entrypoint", "python3", image_digest,
             "-c", MAINTENANCE_PROGRAM, operation, submission, place]
    return argv


def _created(run, argv, name):
    """The container the engine created, or a refusal that created nothing.

    ONE IDENTITY, READ FROM THE ENGINE'S OWN ANSWER. `create` prints the
    container id; anything else -- a non-zero status, no line, several lines --
    is a create this manager cannot correlate, and an uncorrelated container is
    the one thing the two-act launch exists to prevent.
    """
    answered = custody._settled(run, argv, seconds=MAINTENANCE_ACT_SECONDS,
                                what="the maintenance create")
    if answered["status"] != 0:
        oci._denied(f"the engine refused to create the maintenance container "
                    f"{name_value(name)}: "
                    f"{name_value(answered['stderr'][:oci.MAX_DIAGNOSTIC])}; "
                    f"nothing was started and no resource was exposed")
    lines = [one.strip() for one in answered["stdout"].splitlines()
             if one.strip()]
    if len(lines) != 1:
        oci._denied(f"the engine answered {len(lines)} identities for one "
                    f"maintenance create; a container this manager cannot name "
                    f"exactly is one it cannot bind, admit or prove gone")
    return boundaries.identity(lines[0], "a created runtime id")


def _ceased(engine, run, *, name, container):
    """PROVE this exact container and every writer it left are gone.

    THE HOST'S OWN DECISION, SEPARATE FROM THE REPORT. TOK-5 as amended:
    confirmed termination of the exact outgoing container precedes the return,
    and a naturally exited container qualifies only after the same positive
    checks. So the exit status the program printed decides nothing here.

    `custody._reclaimed` IS THE PROOF PATH, reused rather than restated: stop,
    force-remove, then require this engine's own absence sentence to NAME this
    identity. An acknowledgement is not an absence.

    Answers the typed cessation evidence `tokens.returned` requires, or raises.
    Removing the container is what makes "no writable helper survives" a fact
    about the mount rather than a hope: the one process that held it is gone
    and its identity is proved absent.
    """
    custody._reclaimed(engine, run, name=name, runtime_id=container)
    return True


def _refuse_if_governed(control, domain, runtime_id):
    """Refuse to end a runtime an OUTSTANDING generation has bound.

    R1. `custody._reconciled` decides that a candidate is a container of THIS
    MANAGER'S KIND -- same derived name, same image. That is not the same
    question as "is anybody governing it", and the difference matters here
    because the answer to the second question is in this manager's own journal:
    a generation that is outstanding and has bound this exact container is an
    actor whose token still permits it to write.

    So the destructive step is conditioned on the journal rather than on the
    name. Read outside every transaction, like every other journal read this act
    takes before acting.
    """
    for held in tokens.outstanding(control, domain):
        current = tokens.token_of(control, domain, held["generation"])
        if current["container"] != runtime_id:
            continue
        raise ContractRefusal(
            "refused", "precondition",
            f"container {name_value(runtime_id)} answers to this act's derived "
            f"name AND is bound to outstanding generation "
            f"{held['generation']} of {name_value(domain)} (operation "
            f"{name_value(held['operation'])}, execution "
            f"{name_value(held['execution'])}"
            + (", activation admitted and unsettled"
               if current["activating"] else "")
            + f"); a derived name is not authority to end a live governed actor, "
              f"so this refuses rather than reclaiming somebody else's execution")


def _closing(control, assignment_id, which, ordinal, domain, operation):
    """Close a window whose act refused BEFORE any container existed.

    R2's other half. A window that stands forever excludes custody, allocation
    and the next preparation, so a refusal that authorized nothing must not leave
    one: there is no effect to reconcile, and a hold about nothing is a hold an
    operator cannot discharge.

    BEST EFFORT AND SILENT ON FAILURE, deliberately: this runs on the way out of
    another refusal, and replacing that refusal with a journal error would hide
    the reason the act stopped. An unclosed window is the SAFE residue -- it
    refuses later acts rather than admitting them.
    """
    try:
        _settled(control, assignment_id, which, ordinal,
                 {"disposition": SETTLED_REFUSED, "domain": domain,
                  "verb": operation,
                  "why": "the act refused before any container existed, so this "
                         "window authorized no effect on the resource"})
    except Exception:                                    # pragma: no cover
        pass


def _abandoned(engine, run, control, assignment_id, which, ordinal, *, domain,
               operation, generation, container, name, why):
    """End the exact runtime a refused act created, and record what is known.

    R2. The order is the one `custody` was corrected into: order the stop, force
    the removal, then require the engine's own absence sentence to NAME this
    identity. Everything here happens OUTSIDE every transaction.

      absence PROVED      -> the orphan is recorded as gone and the window closes;
                             nothing was admitted, so no effect can arrive
      absence UNPROVED    -> the orphan is recorded with that unknown and the
                             window STAYS OPEN, which is the honest hold

    The refusal that brought us here is the one that propagates; this adds
    durable facts to it rather than replacing it.
    """
    proved, observed = True, None
    try:
        custody._reclaimed(engine, run, name=name, runtime_id=container)
    except ContractRefusal as unproved:
        proved, observed = False, str(unproved)
    except Exception as failed:                          # pragma: no cover
        proved, observed = False, type(failed).__name__
    try:
        _orphaned(control, assignment_id, which, ordinal,
                  {"domain": domain, "generation": generation,
                   "verb": operation, "container": container,
                   "helper_identity": name, "why": why,
                   "absence_proved": proved, "observed": observed})
        if proved:
            _settled(control, assignment_id, which, ordinal,
                     {"disposition": SETTLED_ORPHANED, "domain": domain,
                      "generation": generation, "verb": operation,
                      "container": container, "why": why})
    except Exception:                                    # pragma: no cover
        pass


def _mismatch(document, place_name, gid):
    """Why this report is not an account of THIS act, by VALUE, or `None`.

    R3. `_accountable` owns the shape; this owns the values, and the distinction
    is the review's: a document carrying the right members with the right types
    can still describe another object, another mode or another identity.

    Every expected value is composed here from what this manager itself decided
    -- the derived place, this module's mode constant, this module's version and
    the execution identity the create vector declared -- so there is no operand
    a report could satisfy by naming itself.
    """
    from . import workspaces

    if document.get("version") != MAINTENANCE_VERSION:
        return (f"the account declares representation version "
                f"{name_value(document.get('version'))} and this manager "
                f"composes version {MAINTENANCE_VERSION}; a document of another "
                f"representation is not one whose members this build may read")
    if document["place"] != place_name:
        return (f"the account reports preparing {name_value(document['place'])} "
                f"and this act asked for {name_value(place_name)}; an account of "
                f"another object is not an account of this one")
    if document["mode"] != oct(PREPARED_MODE):
        return (f"the account reports mode {name_value(document['mode'])} and "
                f"this manager establishes {oct(PREPARED_MODE)}; the prepared "
                f"object's permissions are the reason the preparation exists")
    declared = workspaces.identity_for(
        workspaces.WorkspaceGroup(gid, workspaces._MINT))
    if list(document["running_as"]) != [declared.uid, declared.gid]:
        return (f"the account says it ran as {document['running_as']!r} and this "
                f"act declared {[declared.uid, declared.gid]!r}; an act that did "
                f"not run as the identity that owns the worker's objects is not "
                f"the act this manager composed")
    return None


def _established_identity(source, place_name):
    """The object identity of what was established, for the durable receipt.

    Recorded so a later reader can compare the prepared object against the
    resource it was prepared inside -- the pre-allocation identity's promise,
    kept as a fact rather than as an argument.
    """
    held = os.lstat(os.path.join(source, place_name))
    return f"{held.st_dev}:{held.st_ino}"


def prepare(engine, run, *, image_digest, store, assignment_id, operation,
            which="workspace", seconds=None):
    """ONE SCOPED MAINTENANCE PREPARATION, performed under a shared token.

    The whole lifecycle, in one act, with nothing executable crossing back.

    WHY THE ORDER IS THE ORDER:

      * the VERB and the ROOT are checked before anything is acquired, because
        `custody_act` learned that the hard way -- a refused verb that had
        already committed a durable hold froze a root having submitted nothing;
      * the ROOT and its GROUP are re-opened from durable state, in this act,
        so no path-bearing object is handed to anybody;
      * a STRANDED container answering to this derived name is reconciled
        BEFORE the token is taken, because a second preparation over a
        directory a first one may still be writing is worse than failing;
      * the TOKEN is acquired and the LAUNCH journalled before the engine is
        asked for anything, which is TOK-4: reserve before launch, because a
        container id may not exist yet;
      * the container is CREATED INERT, BOUND, and its activation ADMITTED,
        and only then STARTED -- so the resource is exposed to a process only
        after the journal says which process, under which generation;
      * the OUTCOME is validated, the CESSATION is proved, and only then is the
        token RETURNED. Three decisions, three refusals, one order.

    NO ENGINE CALL AND NO `lstat` HAPPENS UNDER A WRITE LOCK. DB-2: every
    external observation is taken outside the journal's transactions, and what
    happens inside one is the journal's own work.
    """
    port = run if type(run) is oci.EnginePort else oci.EnginePort(run)
    operation = check_preparation(operation)
    custody.check_custody_root(which)
    place_name = _prepared_name(assignment_id)
    source, gid, recorded = custody._derived_root(store, assignment_id, which)
    name = _maintenance_identity(recorded, assignment_id, which, operation)
    # THE DOMAIN, AND ITS PRE-ALLOCATION IDENTITY, both read from the object
    # this act re-opened -- outside every transaction.
    governed, pre_allocation = _resource_identity(source, place_name)
    domain = tokens.domain_of(MAINTENANCE_KIND, governed)
    # WHAT THIS OPERATION ALREADY DID, READ BEFORE ANY ENGINE CALL.
    #
    # MEASURED DEFECT OF MY OWN, found by asking what a repeat of this act does:
    # `acquire` replays a RETURNED generation, so a second preparation used to
    # get as far as CREATING a container and then refuse at the admission --
    # leaving a container nothing had reclaimed. Stranding a helper on the way
    # out is the exact failure `custody` was corrected for twice, and a refusal
    # that has already created something has not preserved what it refused for.
    #
    # So the journal decides FIRST, and each disposition is named:
    #
    #   nothing recorded            -> this is the act; proceed
    #   outstanding, nothing bound  -> a create whose reply may have been lost;
    #                                  reconcile the derived name and proceed
    #   outstanding, container bound-> a PARTIALLY LAUNCHED act. Recovery, not a
    #                                  second launch, and this facility refuses
    #                                  it with the exact hold named
    #   returned                    -> a completed act; repeating it is not this
    #                                  facility's to authorize
    already = tokens.generation_of(
        store, domain,
        execution=_execution_identity(assignment_id, which),
        operation=_operation_identity(operation, assignment_id, which))
    if already is not None:
        current = tokens.token_of(store, domain, already)
        if current["returned"]:
            raise ContractRefusal(
                "refused", "already-terminal",
                f"generation {already} of {name_value(domain)} performed this "
                f"preparation and has been RETURNED; a returned generation "
                f"authorizes nothing further, and a completed preparation is "
                f"not repeated on the strength of being asked twice")
        if current["container"] is not None:
            raise ContractRefusal(
                "refused", "precondition",
                f"generation {already} of {name_value(domain)} is OUTSTANDING "
                f"with container {name_value(current['container'])} bound and "
                f"its activation "
                f"{'admitted and unsettled' if current['activating'] else 'not admitted'}"
                f"; a partially launched preparation is reconciled rather than "
                f"launched a second time, and this facility does not decide "
                f"that -- the container and the generation are named here so an "
                f"operator or a recovery pass can act on the exact hold")
    # R1: THE WINDOW IS OPENED UNDER THE WRITE LOCK, and this is where the
    # reviewer's probe used to get through. Custody overlap, standing removals
    # and prior maintenance windows are re-read INSIDE `BEGIN IMMEDIATE`; a hold
    # that commits after this returns is refused by the acquisition's own
    # predicate below, so both orderings are covered by a decision rather than by
    # a check.
    ordinal = _admitted(store, assignment_id, which, operation=operation,
                        name=name, domain=domain, pre_allocation=pre_allocation)
    try:
        # WHAT IS ALREADY ANSWERING TO THIS IDENTITY, decided before anything is
        # acquired or launched. `custody._reconciled` refuses every uncertain
        # branch, which is the answer this path wants: one derived identity names
        # one container.
        stranded = custody._reconciled(engine, port, name=name,
                                       image_digest=image_digest)
        if stranded is not None:
            # R1, LAST PARAGRAPH: A DERIVED NAME IS NOT AUTHORITY TO END A LIVE
            # ACTOR. The image check says the container is this manager's kind of
            # container; it does not say nobody is governing it. So the journal is
            # asked first, and a runtime that an OUTSTANDING generation has bound
            # is refused rather than stopped -- ending it would destroy an actor
            # whose token still permits it to write, which is the one thing a
            # reclamation must never do.
            _refuse_if_governed(store, domain, stranded)
            custody._reclaimed(engine, port, name=name, runtime_id=stranded)
        token = tokens.acquire(
            store, domain,
            operation=_operation_identity(operation, assignment_id, which),
            execution=_execution_identity(assignment_id, which),
            # THE ASSOCIATION AND NOT A CLAIM. `acquire` records the attempt this
            # permission is associated with; it writes no attempts row and mints
            # no task claim, and the execution above is provably not a runtime id.
            attempt=assignment_id,
            # R1: THE ACQUISITION ITSELF CARRIES THE CONDITION, evaluated inside
            # its own transaction. DB-1: eligibility, the conflict read and the
            # acquisition are one act; DB-2: the predicate reads the journal and
            # nothing else.
            eligible=_eligible(store, assignment_id, which),
            seconds=MAINTENANCE_SECONDS)
    except BaseException:
        # NOTHING CROSSED, so the window closes rather than standing forever. A
        # refusal here happened before any container existed: the reconciliation
        # either found nothing or proved what it ended absent, and no acquisition
        # was recorded -- so there is no effect for an operator to reconcile and
        # leaving the root excluded would be a hold about nothing.
        _closing(store, assignment_id, which, ordinal, domain, operation)
        raise
    launch = token["operation"]
    tokens.journal_launch(store, token, launch)
    # THE SUBMISSION CORRELATOR IS THE TOKEN'S OWN OWNER, reused rather than
    # drawn: it is already a digest over the domain, operation, execution,
    # acquiring instant and this manager's incarnation, so an echo of it says
    # the document belongs to THIS generation. Nothing here needs entropy, and
    # `uuid` is outside the ruled import set for exactly that reason.
    submission = token["owner"]
    argv = _create_vector(engine, image_digest=image_digest, source=source,
                          gid=gid, name=name, operation=operation,
                          submission=submission, place=place_name)
    generation = token["generation"]
    try:
        container = _created(port, argv, name)
    except BaseException:
        _closing(store, assignment_id, which, ordinal, domain, operation)
        raise
    # R2: THE EXACT CREATED RUNTIME IS THIS ACT'S TO END IF IT CANNOT PROCEED.
    #
    # The reviewer's probe advanced the grant past expiry between the create and
    # the bind: `bind_container` refused -- correctly, because a late binding is
    # exactly what TOK-4 forbids -- and the earlier cut then LEFT the inert
    # container behind with no stop, no removal and no record of its identity.
    # Nothing had been admitted, so no effect was permitted; what was lost was
    # the one moment at which this manager could still name and end it.
    #
    # THE NO-LATE-BIND RULE IS UNTOUCHED. The refusal still propagates and no
    # stale binding is forced to make cleanup possible. What changes is that the
    # container is reconciled OUTSIDE every transaction and, if its absence
    # cannot be proved, the orphan is RECORDED and the window stays open.
    try:
        tokens.bind_container(store, token, container, launch=launch)
        # ADMITTED BEFORE THE START AND NOT AFTER IT. The admission is the
        # durable record that says this exact container may run under this
        # generation; a start that preceded it would be an effect the journal
        # never permitted.
        tokens.admit_activation(store, token, container=container)
    except BaseException as refused:
        _abandoned(engine, port, store, assignment_id, which, ordinal,
                   domain=domain, operation=operation, generation=generation,
                   container=container, name=name, why=str(refused))
        raise
    started = custody._settled(
        port, oci.activation_vector(engine, runtime_id=container),
        seconds=custody.allowed(seconds, MAINTENANCE_ACT_SECONDS),
        what="the maintenance activation")
    if started["status"] != 0:
        # UNKNOWN, AND IT STAYS UNKNOWN. Review-established G1 rule: a caller
        # must NOT settle `started=False` because the start call refused -- the
        # engine is client/server, so a lost reply is compatible with a
        # container that is running. The activation is left in flight, which
        # holds the resource, and the answer says so.
        return _answered(
            operation, generation, container, started["status"], None,
            returned=False,
            diagnostic=f"UNRESOLVED: the engine did not answer the activation "
                       f"of {name_value(container)} positively "
                       f"({name_value(started['stderr'][:oci.MAX_DIAGNOSTIC])})"
                       f", so whether the preparation is running is UNKNOWN. "
                       f"Generation {generation} of {name_value(domain)} stays "
                       f"OUTSTANDING with its launch and container correlated; "
                       f"the activation is unsettled on purpose and this is "
                       f"not an absence proof")
    # THE CONCLUSIVE OUTCOME OF THE ADMITTED ACTIVATION, and only now. The
    # engine answered positively about starting THIS container, which is what
    # `started=True` means -- it is not a claim about what the program did.
    tokens.settle_activation(store, token, container=container, started=True)
    waited = custody._settled(port, oci.wait_vector(engine, runtime_id=container),
                              seconds=custody.allowed(seconds,
                                                      MAINTENANCE_ACT_SECONDS),
                              what="the maintenance wait")
    if waited["status"] != 0:
        return _answered(
            operation, generation, container, waited["status"], None,
            returned=False,
            diagnostic=f"UNRESOLVED: this manager could not learn whether the "
                       f"preparation in {name_value(container)} has ended "
                       f"({name_value(waited['stderr'][:oci.MAX_DIAGNOSTIC])})."
                       f" Generation {generation} of {name_value(domain)} stays "
                       f"OUTSTANDING; a container whose ending is unobserved is "
                       f"not one to prove absent and not one to return a token "
                       f"on")
    # THE CONTAINER'S OWN OUTCOME, read from the wait that named it. Transport and
    # outcome are different facts and this is where they are told apart; an answer
    # this manager cannot read is an unknown rather than a success.
    exit_status, unreadable = _container_exit(waited)
    if unreadable is not None:
        _ceased(engine, port, name=name, container=container)
        return _answered(
            operation, generation, container, None, None, returned=False,
            diagnostic=f"UNRESOLVED: {unreadable}. The container was ended and "
                       f"proved absent, and generation {generation} of "
                       f"{name_value(domain)} stays OUTSTANDING; an execution "
                       f"whose exit nobody established is not a preparation this "
                       f"manager may call done")
    printed = custody._settled(port, oci.logs_vector(engine,
                                                     runtime_id=container),
                               seconds=custody.allowed(seconds,
                                                       MAINTENANCE_ACT_SECONDS),
                               what="the maintenance account")
    document = _document(printed["stdout"]) if printed["status"] == 0 else None
    # THE ANSWER'S STATUS IS THE CONTAINER'S, not the logs command's. My earlier cut
    # carried the LOGS CLI status here, which is how a container that exited 17 came
    # back looking like a clean act: two successful commands ABOUT a failed
    # execution are not a successful execution.
    minted = _answered(operation, generation, container, exit_status,
                       document, returned=False,
                       diagnostic=printed["stderr"][-custody.MAX_DIAGNOSTIC:])
    if exit_status != 0:
        # A KNOWN EXIT IS NOT KNOWN EFFECTS, and review 2026-09-27T14-27-04Z is where
        # I was corrected on exactly this. I had made a nonzero exit a settlement that
        # closed the window and returned the token, reasoning that a known exit plus a
        # proved cessation leaves no uncertainty. Three facts are separate (TOK-8):
        # the container is gone, its exit is known, and what it DID to the tree is
        # not -- a failed act may have left partial output that needs repair (TOK-12).
        #
        # SO THE FAILURE IS RECORDED AND NOTHING IS DISCHARGED. The exact container is
        # still ended and proved absent, because that fact is worth having and costs
        # nothing; the window keeps standing and the token keeps the resource held, so
        # no ordinary replacement takes a tree whose state nobody established. The
        # effect is NOT repeated to obtain a better status.
        # WHETHER THE REPORT IS THIS GENERATION'S, decided by the same three rules
        # the success path uses rather than by shape alone. MEASURED CORRECTION of my
        # own: I first recorded `accounted` from `unaccounted is None`, which is only
        # the SHAPE -- so a well-formed report naming ANOTHER submission was written
        # down as accounted for. On this branch the submission and semantic checks
        # below are never reached, so they are asked here.
        unaccountable = minted.unaccounted
        if unaccountable is None \
                and minted.answer.get("submission") != submission:
            unaccountable = (
                f"the account answers for submission "
                f"{name_value(minted.answer.get('submission'))} and this "
                f"generation submitted {name_value(submission)}")
        if unaccountable is None \
                and minted.answer.get("maintenance") != _REFUSED:
            unaccountable = _mismatch(minted.answer, place_name, gid)
        _ceased(engine, port, name=name, container=container)
        _failed(store, assignment_id, which, ordinal,
                {"domain": domain, "generation": generation,
                 "owner": token["owner"], "verb": operation,
                 "execution": token["execution"], "attempt": token["attempt"],
                 "launch": launch, "container": container,
                 "exit_status": exit_status,
                 "accounted": unaccountable is None,
                 "unaccounted": unaccountable,
                 "report": minted.rendered if unaccountable is None else None,
                 "cessation": "the engine's own absence sentence named this "
                              "container after its removal",
                 "why": "the admitted container ran and exited nonzero; its exit "
                        "and its cessation are known and the state of the "
                        "resource it could have changed is NOT, so this record "
                        "settles nothing"})
        return _answered(
            operation, generation, container, exit_status, document,
            returned=False,
            diagnostic=f"the preparation in {name_value(container)} EXITED "
                       f"{exit_status}, so it did not prepare anything this "
                       f"manager may rely on. The container was ended and proved "
                       f"absent and the failure is recorded durably, but the "
                       f"resource stays HELD: a known exit is not a known effect, "
                       f"and a failed act may have left partial output that needs "
                       f"repair. Generation {generation} of {name_value(domain)} "
                       f"stays OUTSTANDING with maintenance window {ordinal} "
                       f"standing; the effect was not repeated to obtain a better "
                       f"status")
    # AND THE ECHO MUST BE THIS GENERATION'S. An accountable result for the
    # right verb is still an account of SOME act; the submission is what says
    # which one -- and here it is the token owner, so a document from another
    # generation accounts for nothing.
    if minted.answer is not None \
            and minted.answer.get("submission") != submission:
        return _answered(
            operation, generation, container, printed["status"], None,
            returned=False,
            diagnostic=f"the account read from {name_value(container)} answers "
                       f"for submission "
                       f"{name_value(minted.answer.get('submission'))} and "
                       f"this generation submitted {name_value(submission)}; "
                       f"an account of another submission is not an account of "
                       f"this one. Generation {generation} of "
                       f"{name_value(domain)} stays OUTSTANDING")
    if minted.unaccounted is not None or minted.answer.get("maintenance") \
            == _REFUSED:
        # THE OUTCOME IS NOT ESTABLISHED, so the resource stays held. The
        # container is still reconciled -- leaving one holding the mount is the
        # worse outcome -- but the token is not returned, because an outcome
        # nobody can account for is the unknown this token exists to hold.
        _ceased(engine, port, name=name, container=container)
        why = (minted.unaccounted if minted.unaccounted is not None
               else f"the preparation refused: "
                    f"{name_value(minted.answer.get('why'))}")
        return _answered(
            operation, generation, container, printed["status"], document,
            returned=False,
            diagnostic=f"UNRESOLVED: {why}. The container was ended and proved "
                       f"absent, and generation {generation} of "
                       f"{name_value(domain)} stays OUTSTANDING because this "
                       f"manager cannot say the preparation happened")
    # R3: THE SEMANTIC VALUES, NOT ONLY THEIR TYPES. `_accountable` proves the
    # document has this verb's members with this verb's types; it cannot say the
    # act prepared THE OBJECT THIS ACT ASKED FOR. So the version, the place, the
    # mode and the execution identity are compared against what this manager
    # itself composed -- a report that names another object, another mode or
    # another identity is an account of something else.
    semantic = _mismatch(minted.answer, place_name, gid)
    if semantic is not None:
        _ceased(engine, port, name=name, container=container)
        return _answered(
            operation, generation, container, printed["status"], document,
            returned=False,
            diagnostic=f"UNRESOLVED: {semantic}. The container was ended and "
                       f"proved absent, and generation {generation} of "
                       f"{name_value(domain)} stays OUTSTANDING; a report whose "
                       f"values are not the ones this act composed settles "
                       f"nothing")
    # THE PREPARED OBJECT, VALIDATED AGAINST THE PRE-ALLOCATION IDENTITY. This
    # is the mapping the identity promised: the established object's PARENT must
    # be the very object this token governs, so what was prepared is provably
    # inside the resource rather than merely named like it.
    established = os.path.join(source, place_name)
    try:
        held = os.lstat(established)
    except FileNotFoundError:
        held = None
    if held is None or stat.S_ISLNK(held.st_mode) \
            or not stat.S_ISDIR(held.st_mode) \
            or f"{os.lstat(source).st_dev}:{os.lstat(source).st_ino}" \
            != pre_allocation.rsplit("/", 1)[0]:
        _ceased(engine, port, name=name, container=container)
        return _answered(
            operation, generation, container, printed["status"], document,
            returned=False,
            diagnostic=f"the preparation reported establishing "
                       f"{name_value(place_name)} and this manager cannot "
                       f"confirm it inside the object generation {generation} "
                       f"of {name_value(domain)} governs (pre-allocation "
                       f"identity {name_value(pre_allocation)}); the resource "
                       f"stays held rather than accepted on the report")
    # CESSATION, PROVED, AND ONLY THEN THE RETURN.
    _ceased(engine, port, name=name, container=container)
    # R3: THE AUTHORITATIVE SETTLEMENT IS COMMITTED BEFORE THE TOKEN GOES BACK.
    #
    # Three facts, three acts, in this order: the report validated, the exact
    # container proved absent, and only then a durable receipt naming what was
    # prepared. The token return is LAST, because it is the act that lets another
    # holder in -- and a resource handed on before its outcome was recorded would
    # leave the next holder unable to learn what happened to it.
    _settled(store, assignment_id, which, ordinal,
             {"disposition": SETTLED_PREPARED, "domain": domain,
              "generation": generation, "owner": token["owner"],
              "verb": operation, "execution": token["execution"],
              "attempt": token["attempt"], "launch": launch,
              "container": container, "place": place_name,
              "pre_allocation": pre_allocation,
              "established": minted.answer["established"],
              "mode": minted.answer["mode"], "exit_status": exit_status,
              "object_identity": _established_identity(source, place_name),
              "running_as": list(minted.answer["running_as"]),
              "cessation": "the engine's own absence sentence named this "
                           "container after its removal"})
    tokens.returned(store, token,
                    cessation={"domain": domain, "generation": generation,
                               "launch": launch, "container": container,
                               # A LIST RATHER THAN A TUPLE, because the
                               # cessation boundary takes exact JSON data: the
                               # surviving-writer set is empty because the one
                               # process that held the mount was removed and
                               # proved absent above.
                               "stopped": True, "helpers": []})
    return _answered(operation, generation, container, printed["status"],
                     document, returned=True,
                     diagnostic=printed["stderr"][-custody.MAX_DIAGNOSTIC:])
