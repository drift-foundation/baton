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
    ESTABLISH_RESULT_ROOT: {"submission": str, "place": str,
                            "established": bool, "mode": str,
                            "running_as": list},
}

# THE PROGRAM'S OWN TYPED REFUSAL, which is the other document it can print. It
# is accountable -- it says the act did not happen and why -- and it is never a
# successful account of the verb that was asked for.
_REFUSED = "refused"
_REFUSAL = {"submission": str, "why": str}

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
#     MAINTENANCE_ACT_SECONDS + MAINTENANCE_STOP_SECONDS (390) < 900
#
# so the whole act plus its reclamation is bounded strictly inside the grant,
# and an ordinary slow act is accounted for rather than lost.
MAINTENANCE_SECONDS = tokens.LIFETIME_SECONDS
PREPARE_SECONDS = 300
MAINTENANCE_ACT_SECONDS = PREPARE_SECONDS + 60
MAINTENANCE_STOP_SECONDS = tokens.STOP_GRACE_SECONDS

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


def answered(document):
    sys.stdout.write(json.dumps(document, sort_keys=True) + "\n")
    sys.stdout.flush()


def refuse(why, code):
    """THE PROGRAM'S OWN ACCOUNT OF NOT ACTING, which is still an account."""
    answered({"maintenance": "refused", "submission": SUBMISSION, "why": why})
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
answered({"maintenance": VERB, "submission": SUBMISSION, "place": PLACE,
          "established": established,
          "mode": oct(stat.S_IMODE(final.st_mode)),
          "running_as": [os.getuid(), os.getgid()]})
'''

MAINTENANCE_PROGRAM = _PROGRAM_SOURCE.replace("__SECONDS__",
                                              str(PREPARE_SECONDS))


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

        `custody`'s three conditions plus the one this facility adds: a
        preparation whose token is still outstanding is not a completed
        preparation, however good its document looked.
        """
        return (self._answer is not None and self._unaccounted is None
                and self._returned)


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
    # THE EXISTING CUSTODY HOLD IS HONOURED, AND IT IS NOT REPLACED BY THIS
    # TOKEN. An unreconciled uncertainty episode over either overlapping root
    # says a submitted request may still land inside this tree; a preparation
    # that acted anyway would be the second submission that whole exclusion
    # exists to refuse.
    standing = custody._standing_overlap(store, assignment_id, which)
    if standing is not None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(assignment_id)}'s "
            f"{standing['held']['root']} root carries unreconciled uncertainty "
            f"episode {standing['episode']!r}, whose helper is "
            f"{name_value(standing['held']['helper_identity'])}; a preparation "
            f"is not performed inside a tree an earlier act may still be "
            f"writing, and that episode is reconciled rather than acted past")
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
    # WHAT IS ALREADY ANSWERING TO THIS IDENTITY, decided before anything is
    # acquired or launched. `custody._reconciled` refuses every uncertain
    # branch, which is the answer this path wants: one derived identity names
    # one container.
    stranded = custody._reconciled(engine, port, name=name,
                                   image_digest=image_digest)
    if stranded is not None:
        custody._reclaimed(engine, port, name=name, runtime_id=stranded)
    token = tokens.acquire(
        store, domain,
        operation=_operation_identity(operation, assignment_id, which),
        execution=_execution_identity(assignment_id, which),
        # THE ASSOCIATION AND NOT A CLAIM. `acquire` records the attempt this
        # permission is associated with; it writes no attempts row and mints no
        # task claim, and the execution above is provably not a runtime id.
        attempt=assignment_id,
        seconds=MAINTENANCE_SECONDS)
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
    container = _created(port, argv, name)
    tokens.bind_container(store, token, container, launch=launch)
    # ADMITTED BEFORE THE START AND NOT AFTER IT. The admission is the durable
    # record that says this exact container may run under this generation; a
    # start that preceded it would be an effect the journal never permitted.
    tokens.admit_activation(store, token, container=container)
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
    printed = custody._settled(port, oci.logs_vector(engine,
                                                     runtime_id=container),
                               seconds=custody.allowed(seconds,
                                                       MAINTENANCE_ACT_SECONDS),
                               what="the maintenance account")
    document = _document(printed["stdout"]) if printed["status"] == 0 else None
    minted = _answered(operation, generation, container, printed["status"],
                       document, returned=False,
                       diagnostic=printed["stderr"][-custody.MAX_DIAGNOSTIC:])
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
