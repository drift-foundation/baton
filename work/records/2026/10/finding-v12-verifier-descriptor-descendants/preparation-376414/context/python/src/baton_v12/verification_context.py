"""The DECLARED verification context, decided before any view exists.

W321776, under `work/records/2026/09/finding-v12-complete-verification-context/
findings/finding-paired-context-delivery/`, against the accepted packet in
`findings/finding-context-packet/` (W321780, checkpoint
`6348161e608187393e45454db63c192a93f6deb3`).

WHAT THIS IS. The half of the paired correction that both holders can decide
from the sealed task and the sealed set ALONE -- Stage A -- plus the closed
vocabulary their durable records share. The worker and the independent operator
each materialize their own private verification view; this module is what they
agree about BEFORE either one exists, so the two cannot disagree by having
written the same rule twice.

WHAT IT IS EMPHATICALLY NOT:

  NOT A MATERIALIZER. It creates nothing, reads no view, opens no path and
  touches no candidate. Stage B -- the view preflight -- is decidable only once
  a view exists and belongs to the party that built one.
  NOT A PROFILE VOCABULARY. `source_profiles.checkout` owns the three profile
  words and the base pairing, and this module ASKS that package through an
  injected operand rather than restating it. A second copy of the pairing is a
  second decision-maker, which is the defect the profile package's own docstring
  was written to prevent.
  NOT A READER OF THE HOST. Every answer comes from the task document and the
  two sealed maps the caller supplies.
  NOT A WIDENING OF `/2`. `baton.dogfood-task/2` is frozen: it carries
  `source_profile` and `declared_base` (W71917) and its name is occupied by that
  shape. The declared context arrives as a NEW version, and the refusal
  direction runs the right way -- an older holder REFUSES the new member rather
  than ignoring it.

WHY IT TRAVELS AS A TOP-LEVEL MODULE. It imports nothing from `baton_v12`, so
the worker image copies it under its own name exactly as
`baton_v12.source_profiles` and `baton_v12.attempt_log_format` do
(`v12/worker/Dockerfile.claude`). A worker that could import the manager is a
worker one bug away from holding the manager's capabilities; a shared contract
that imports no manager is not that, and
`tests/manager/test_verification_context` holds the separation in both
directions rather than leaving it to this paragraph.

THE TWO KINDS OF FACT, kept apart, which is the correction the packet's
lifecycle trace exists to carry:

  a LAUNCH CONSTRAINT is true at sealing, from the task and the sealed inputs
  alone -- the profile, the declared base, the pinned bytes, the paths;
  a CANDIDATE OBSERVATION is true only after the provider finishes -- the entry
  head, the changed paths, the deletions, the exclusion disclosure.

A sealed task that carried an observation would be a task claiming to know what
its own turn had not done yet, and rewriting the pre-claim input binding to
insert one afterwards is what DESIGN ART-3 forbids. So `entry_head`,
`tree_digest`, `changed`, `changed_paths`, `removed` and `collection` are
REFUSED in the sealed context, by name, and the published result carries them.

THE STAGE-A CAUSE MAPPING IS THIS MODULE'S READING, and it is stated here
because the packet's Stage-A table names the refusals without naming their
causes. The context document admits exactly four: `missing-input`,
`invalid-layout`, `materialization` and `start-failure`. `materialization` and
`start-failure` cannot be reached before anything is materialized or started,
so Stage A produces exactly two:

  `missing-input`    a declared input or a pinned path the SEAL does not hold,
                     or holds at other bytes -- the question is about the seal,
                     decided against the seal;
  `invalid-layout`   every declaration fault -- a path that would escape its
                     root, an overlap, a malformed digest, a closed member
                     missing or unknown, an observation in a constraint, a
                     profile and base that disagree.

A reviewer who reads that split differently is reading a choice, not a quoted
rule, and `PROGRESS.md` says so in the dossier.

AND A DETAIL NAMES A MEMBER, NEVER A VALUE. `detail` is the member locator or
the declared input name and nothing else: no path the caller supplied, no
digest, no child output, no exception prose. A refusal that interpolated the
offending value would publish the untrusted bytes it was refusing -- which is
how a bounded structural fact becomes a channel.
"""

import re

__all__ = ["CAUSES", "COMMANDS", "CONTEXT_SCHEMA", "ContextRefusal",
           "EVIDENCE_SCHEMA", "FAILED", "INVALID_LAYOUT", "LEGACY_PROPOSAL",
           "LEGACY_TASK_SCHEMA", "MATERIALIZATION", "MISSING_INPUT",
           "MalformedOutcome", "NOT_RUN", "OBSERVATION_MEMBERS", "PASSED",
           "PROPOSAL_SCHEMA", "READY", "REFUSED", "START_FAILURE",
           "STATIC_STAGE", "TASK_SCHEMA", "TIMED_OUT", "VIEW_STAGE",
           "check_outcome", "generation", "held", "import_path", "ready",
           "refused", "reported_command", "verdict"]

# THE TASK GENERATIONS. `/2` is frozen and untouched; `/3` is `/2` plus one
# member. Both constants live here because the refusal direction is a statement
# about the PAIR, and a holder that knew only its own generation could not make
# it.
LEGACY_TASK_SCHEMA = "baton.dogfood-task/2"
TASK_SCHEMA = "baton.dogfood-task/3"

# The durable shapes. The context is its own document because it is the thing
# both holders publish and a consumer compares; the proposal and the evidence
# are the two holders' separate observations.
CONTEXT_SCHEMA = "baton.dogfood-context/1"
PROPOSAL_SCHEMA = "baton.dogfood-proposal/3"
EVIDENCE_SCHEMA = "baton.dogfood-operator-evidence/1"
LEGACY_PROPOSAL = "baton.dogfood-proposal/2"

READY = "ready"
REFUSED = "refused"

STATIC_STAGE = "static"
VIEW_STAGE = "view"
STAGES = (STATIC_STAGE, VIEW_STAGE)

MISSING_INPUT = "missing-input"
INVALID_LAYOUT = "invalid-layout"
MATERIALIZATION = "materialization"
START_FAILURE = "start-failure"
CAUSES = (MISSING_INPUT, INVALID_LAYOUT, MATERIALIZATION, START_FAILURE)

NOT_RUN = "not-run"
PASSED = "passed"
FAILED = "failed"
TIMED_OUT = "timed-out"
COMMANDS = (NOT_RUN, PASSED, FAILED, TIMED_OUT)

# The members a SEALED task may not carry, by name. Each one is something only
# the finished turn knows.
OBSERVATION_MEMBERS = ("entry_head", "tree_digest", "changed", "changed_paths",
                       "removed", "collection")

# The closed member set of `verification_context`. Version agreement means both
# holders accept the SAME document, so an unknown member is a refusal rather
# than something one holder ignores and the other reads.
CONTEXT_MEMBERS = ("working_directory", "candidate_destination", "candidate",
                   "import_roots", "required_paths", "inputs")
CANDIDATE_MEMBERS = ("profile", "declared_base", "pins")
PIN_MEMBERS = ("path", "content_digest")
INPUT_MEMBERS = ("name", "destination", "content_digest", "bytes")

_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
_NAME = re.compile(r"\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


class ContextRefusal(Exception):
    """One closed cause, one bounded member locator, and no value.

    It carries the stage it was decided at so a caller can publish the document
    without re-deciding that, and `document()` is the only way the refusal
    becomes durable -- there is no path from here to a record that does not go
    through the closed vocabulary.
    """

    def __init__(self, cause, detail, *, stage=STATIC_STAGE):
        assert cause in CAUSES, cause
        assert stage in STAGES, stage
        super().__init__(f"{stage}/{cause}: {detail}")
        self.cause = cause
        self.detail = detail
        self.stage = stage

    def document(self):
        return refused(self.cause, self.detail, stage=self.stage)


class MalformedOutcome(Exception):
    """A PEER'S record that is not one of the five legal combinations.

    Deliberately not a `ContextRefusal`: a context refusal is this holder's own
    answer about its own run, and this is a reader declining to interpret
    somebody else's published document. Conflating them would let a malformed
    peer record arrive as if this holder had refused its own context.
    """


def ready():
    """The context outcome when every Stage-A and Stage-B question answered."""
    return {"schema": CONTEXT_SCHEMA, "outcome": READY, "stage": None,
            "cause": None, "detail": None}


def refused(cause, detail, *, stage):
    """Exactly one cause, and the stage that could see it."""
    if cause not in CAUSES:
        raise MalformedOutcome(f"{cause!r} is not one of the four causes")
    if stage not in STAGES:
        raise MalformedOutcome(f"{stage!r} is not one of the two stages")
    if not isinstance(detail, str) or not detail:
        raise MalformedOutcome("a refusal names the member that failed")
    return {"schema": CONTEXT_SCHEMA, "outcome": REFUSED, "stage": stage,
            "cause": cause, "detail": detail}


def generation(task):
    """Which generation this task is, with the refusal direction enforced.

    THE DIRECTION IS THE POINT. A `/2` holder offered a `/3` member refuses --
    it does not ignore the member and run anyway, because running anyway is
    exactly the outcome where an operator believes a declared context was
    honoured by a holder that never read it. And a `/3` task with the member
    absent refuses too: a generation that exists to declare the context is not
    satisfied by omitting it.
    """
    if not isinstance(task, dict):
        raise ContextRefusal(INVALID_LAYOUT, "task")
    schema = task.get("schema")
    carried = "verification_context" in task
    if schema == LEGACY_TASK_SCHEMA:
        if carried:
            raise ContextRefusal(INVALID_LAYOUT, "verification_context")
        return LEGACY_TASK_SCHEMA
    if schema == TASK_SCHEMA:
        if not carried:
            raise ContextRefusal(INVALID_LAYOUT, "verification_context")
        return TASK_SCHEMA
    raise ContextRefusal(INVALID_LAYOUT, "schema")


def held(task, *, sealed, pinned, pairing):
    """STAGE A: everything decidable from the task and the two sealed maps.

    Answers `ready()` or raises `ContextRefusal`. **Nothing is materialized
    either way** -- this function has no way to materialize anything, which is
    the structural form of the packet's requirement that a Stage-A refusal
    leaves the view unbuilt.

    `sealed` is the declared immutable input set the manager sealed, keyed by
    `name`; `pinned` is the sealed candidate bytes, keyed by the
    candidate-relative path. Two maps rather than one because the two questions
    are keyed differently -- an input is addressed by name and a pin by path --
    and a single map would have to invent one key for both. The packet's seal
    holds both facts; this module asks each against its own keyed set.

    `pairing(profile, declared)` is `checkout_plan`'s own rule, injected. It
    raises for a profile outside the package's vocabulary and for the two
    disagreements the package refuses: a generic profile carrying a base, and a
    version-control profile without one. ONLY the single call is guarded, and
    the exception's own text never reaches the refusal.
    """
    if generation(task) == LEGACY_TASK_SCHEMA:
        # A `/2` task declares no context, so there is no Stage A to run. The
        # caller asked the wrong question of the wrong generation.
        raise ContextRefusal(INVALID_LAYOUT, "schema")
    _closed(task.get("verification"), "verification")
    context = task["verification_context"]
    if not isinstance(context, dict):
        raise ContextRefusal(INVALID_LAYOUT, "verification_context")
    _members(context, CONTEXT_MEMBERS, "verification_context")
    _no_observations(context, "verification_context")

    candidate = context["candidate"]
    if not isinstance(candidate, dict):
        raise ContextRefusal(INVALID_LAYOUT, "verification_context.candidate")
    _members(candidate, CANDIDATE_MEMBERS, "verification_context.candidate")
    _no_observations(candidate, "verification_context.candidate")
    try:
        pairing(candidate["profile"], candidate["declared_base"])
    except Exception:
        # THE MEMBER, NOT THE MESSAGE. Which of the two the package objected to
        # is not distinguishable without reading its prose, so the refusal
        # names the pair -- and a reader who needs more asks the package.
        raise ContextRefusal(
            INVALID_LAYOUT,
            "verification_context.candidate.profile+declared_base") from None
    # AND THE TWO PLACES THE TASK NAMES THEM MUST AGREE, which is this
    # module's reading rather than a quoted rule and is recorded as such in
    # the dossier. `/3` is `/2` plus one member, so `source_profile` and
    # `declared_base` keep their `/2` meaning AND the context's candidate
    # names them again for the holder that reads only the context. Two
    # spellings of one fact that may disagree is the defect the derived import
    # path exists to prevent, one member over: a holder reading the task would
    # check out one revision while a holder reading the context verified
    # another, and both would believe they agreed.
    if candidate["profile"] != task.get("source_profile"):
        raise ContextRefusal(INVALID_LAYOUT,
                             "verification_context.candidate.profile")
    if candidate["declared_base"] != task.get("declared_base"):
        raise ContextRefusal(INVALID_LAYOUT,
                             "verification_context.candidate.declared_base")

    destination = _contained(context["candidate_destination"],
                             "verification_context.candidate_destination")
    working = _contained(context["working_directory"],
                         "verification_context.working_directory")
    # `working_directory` MAY LIE INSIDE THE CANDIDATE and does in the packet's
    # own layout: the command runs in the candidate's Python subtree. That is
    # not the overlap VER-2 refuses, which is about a sealed INPUT destination
    # and the candidate -- where indistinguishable bytes would let verification
    # feed its own fixtures into the proposal.
    del working

    for index, root in enumerate(_ordered(context["import_roots"],
                                          "verification_context.import_roots")):
        _contained(root, f"verification_context.import_roots[{index}]")
    for index, path in enumerate(
            _ordered(context["required_paths"],
                     "verification_context.required_paths")):
        _contained(path, f"verification_context.required_paths[{index}]")

    _pins(candidate["pins"], pinned=pinned)
    _inputs(context["inputs"], destination=destination, sealed=sealed)
    return ready()


def import_path(context):
    """The derived import path: `import_roots` joined to `working_directory`.

    AND NOTHING ELSE, which is the whole of why this function exists. September
    reached `PYTHONPATH=src` with a hand-set shell variable, and a hand-set
    variable is not a contract: nothing stated what it should be, so nothing
    could disagree with it. Both holders derive this same closed value from the
    same declaration, no ambient entry is inherited, and the argv carries no
    environment assignment -- an argv that carried one would be a second,
    disagreeing source of one fact.

    The caller joins the result to the view root it materialized. This module
    does not know where that is and must not: a contract that resolved host
    paths would be deciding where a view lives.
    """
    working = context["working_directory"]
    return [f"{working}/{one}" for one in context["import_roots"]]


def reported_command(result):
    """What a result SAYS about its command, with `/2`'s silence preserved.

    A `/2` result carries no `context` and no `command`. Its absence reads as
    "this version could not say" -- `None` -- and NEVER as `not-run` and never
    as `passed`. That is the same refusal direction as the task, pointed at
    results: a consumer that defaulted the missing member would be reporting a
    verdict no holder ever published.
    """
    if not isinstance(result, dict):
        raise MalformedOutcome("a result is a document")
    if result.get("schema") == LEGACY_PROPOSAL:
        if "context" in result or "command" in result:
            raise MalformedOutcome(
                "a /2 result carrying /3 members is not a /2 result")
        return None
    if result.get("schema") not in (PROPOSAL_SCHEMA, EVIDENCE_SCHEMA):
        raise MalformedOutcome("an unknown result generation says nothing")
    check_outcome(result.get("context"), result.get("command"),
                  result.get("exit_status"))
    return result["command"]


def check_outcome(context, command, exit_status):
    """THE FIVE LEGAL COMBINATIONS, closed, and every other one refused.

        ready    / passed    / 0                -> verdict: passed
        ready    / failed    / nonzero integer  -> verdict: failed
        ready    / timed-out / null             -> no verdict
        ready    / not-run   / null             -> no verdict
        refused  / not-run   / null             -> no verdict

    `passed` may not carry a null or nonzero status; `failed` may not carry `0`
    or null; a refusal may never carry a command verdict; `not-run` and
    `timed-out` may never carry a status. A verdict exists in the first two rows
    only -- the other three preserve the candidate and assert nothing about it.

    `True` is not `1` here. `isinstance(True, int)` is true in Python, so a
    status of `True` would otherwise satisfy "nonzero integer" and publish a
    boolean as a child's exit code.
    """
    if not isinstance(context, dict) or context.get("schema") != CONTEXT_SCHEMA:
        raise MalformedOutcome("a result carries one context document")
    outcome = context.get("outcome")
    if outcome == READY:
        if (context.get("cause") is not None
                or context.get("stage") is not None):
            raise MalformedOutcome("a ready context names no cause and no "
                                   "stage")
    elif outcome == REFUSED:
        if context.get("cause") not in CAUSES:
            raise MalformedOutcome("a refusal carries exactly one of the four "
                                   "causes")
        if context.get("stage") not in STAGES:
            raise MalformedOutcome("a refusal names the stage that saw it")
        if not isinstance(context.get("detail"), str) or not context["detail"]:
            raise MalformedOutcome("a refusal names the member that failed")
    else:
        raise MalformedOutcome("a context is ready or refused")
    if command not in COMMANDS:
        raise MalformedOutcome("a command is one of the four words")
    if outcome == REFUSED and command != NOT_RUN:
        raise MalformedOutcome("a refused context never carries a command "
                               "verdict")
    if command == PASSED:
        if not _status(exit_status) or exit_status != 0:
            raise MalformedOutcome("passed carries the zero the child supplied")
    elif command == FAILED:
        if not _status(exit_status) or exit_status == 0:
            raise MalformedOutcome("failed carries the nonzero status the "
                                   "child supplied")
    elif exit_status is not None:
        raise MalformedOutcome(f"{command} carries no status, because no child "
                               f"supplied one")
    return None


def verdict(context, command, exit_status):
    """`passed`, `failed`, or `None` when the record asserts nothing.

    A verdict about the candidate comes ONLY from a command that started in a
    ready context. `refused`, `not-run` and `timed-out` preserve the candidate
    and say nothing about whether it is correct -- and a context fault that
    arrived as `failed` would be reporting the context as evidence about the
    code, which is the confusion the two-stage split exists to prevent.
    """
    check_outcome(context, command, exit_status)
    if context["outcome"] == READY and command in (PASSED, FAILED):
        return command
    return None


def _status(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _closed(verification, what):
    """The argv: a non-empty list of non-empty strings, and nothing else."""
    if not isinstance(verification, list) or not verification:
        raise ContextRefusal(INVALID_LAYOUT, what)
    for index, one in enumerate(verification):
        if not isinstance(one, str) or not one:
            raise ContextRefusal(INVALID_LAYOUT, f"{what}[{index}]")


def _members(document, closed, what):
    for name in closed:
        if name not in document:
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.{name}")
    for name in document:
        if name not in closed:
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.{name}"
                                 if _NAME.match(str(name)) else what)


def _no_observations(document, what):
    for name in OBSERVATION_MEMBERS:
        if name in document:
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.{name}")


def _ordered(value, what):
    if not isinstance(value, list):
        raise ContextRefusal(INVALID_LAYOUT, what)
    return value


def _contained(value, what):
    """One relative, canonical, contained path -- or a refusal naming it.

    Absolute and `~` paths are refused because their meaning would depend on
    the host that read them, and `.`, `..` and empty segments escape whatever
    root they are joined to. The canonical form is required rather than
    normalized: `a//b` and `a/./b` normalize to the same place, so accepting
    both would let two spellings of one path be two declared members.
    """
    if not isinstance(value, str) or not value:
        raise ContextRefusal(INVALID_LAYOUT, what)
    if value.startswith("/") or value.startswith("~") or "\0" in value:
        raise ContextRefusal(INVALID_LAYOUT, what)
    for segment in value.split("/"):
        if segment in ("", ".", ".."):
            raise ContextRefusal(INVALID_LAYOUT, what)
    return value


def _within(inner, outer):
    """Is `inner` the same place as `outer`, or inside it?

    Compared by SEGMENTS rather than by prefix, because `candidate` is not a
    prefix match for `candidate-sealed` and a string prefix would read it as
    one -- refusing a declaration that overlaps nothing.
    """
    one = inner.split("/")
    two = outer.split("/")
    return one[:len(two)] == two


def _pins(pins, *, pinned):
    """The pinned candidate bytes: ordered, contained, unique, and SEALED.

    A pin is decidable at sealing -- the path exists, its digest is measured --
    which is why it survives the constraint/observation split while `changed`
    and `removed` do not. Nothing about a pin depends on what the provider will
    do; it names bytes the task requires UNCHANGED.
    """
    seen = set()
    for index, pin in enumerate(_ordered(pins,
                                         "verification_context.candidate.pins")):
        what = f"verification_context.candidate.pins[{index}]"
        if not isinstance(pin, dict):
            raise ContextRefusal(INVALID_LAYOUT, what)
        _members(pin, PIN_MEMBERS, what)
        path = _contained(pin["path"], f"{what}.path")
        if not isinstance(pin["content_digest"], str) \
                or not _DIGEST.match(pin["content_digest"]):
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.content_digest")
        if path in seen:
            # Two digests for one path is not one constraint.
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.path")
        seen.add(path)
        if path not in pinned:
            raise ContextRefusal(MISSING_INPUT, f"{what}.path")
        if pinned[path] != pin["content_digest"]:
            raise ContextRefusal(MISSING_INPUT, f"{what}.content_digest")


def _inputs(inputs, *, destination, sealed):
    """The declared immutable inputs, against the SEAL rather than a view.

    THE OVERLAP REFUSAL IS VER-2's AND IT RUNS BOTH WAYS. A sealed input landing
    under the candidate is indistinguishable from candidate bytes, so
    verification could add fixtures to the proposal; a candidate landing under
    an input destination is the same confusion with the names swapped. A path
    the gate must read from INSIDE the candidate is a `candidate.pins` entry,
    not an input destination.
    """
    seen_names = set()
    seen_places = set()
    for index, one in enumerate(_ordered(inputs,
                                         "verification_context.inputs")):
        what = f"verification_context.inputs[{index}]"
        if not isinstance(one, dict):
            raise ContextRefusal(INVALID_LAYOUT, what)
        _members(one, INPUT_MEMBERS, what)
        name = one["name"]
        if not isinstance(name, str) or not _NAME.match(name):
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.name")
        if name in seen_names:
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.name")
        seen_names.add(name)
        place = _contained(one["destination"], f"{what}.destination")
        if place in seen_places:
            # The second would silently overwrite the first.
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.destination")
        seen_places.add(place)
        if _within(place, destination) or _within(destination, place):
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.destination")
        digest = one["content_digest"]
        if not isinstance(digest, str) or not _DIGEST.match(digest):
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.content_digest")
        if not isinstance(one["bytes"], int) or isinstance(one["bytes"], bool) \
                or one["bytes"] < 0:
            raise ContextRefusal(INVALID_LAYOUT, f"{what}.bytes")
        # DECIDED AGAINST THE SEAL. An input nobody sealed is `missing-input`
        # here, before materialization -- not a surprise in a half-built view.
        held_seal = sealed.get(name)
        if held_seal is None:
            raise ContextRefusal(MISSING_INPUT, f"{what}.name")
        if held_seal.get("content_digest") != digest:
            raise ContextRefusal(MISSING_INPUT, f"{what}.content_digest")
        if held_seal.get("bytes") != one["bytes"]:
            raise ContextRefusal(MISSING_INPUT, f"{what}.bytes")
