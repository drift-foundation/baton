"""One created Job's own task document, composed from the installed one.

W363066, the bounded prerequisite W361912 R3 discovered. A Job created from a
template retained its caller's statement, acceptance criteria and selected work
scope as provenance and delivered the task the DEPLOYMENT installed, because
three owned facts line up that way:

  * `single_worker._task_bytes(given["task_document"],
    manifest["human_contract"])` reads the task once at static preflight from
    the deployment's configured path and holds it as immutable bytes;
  * `stage_execution._Stage.prepare_context` forwards exactly
    `worker.given["task_bytes"]`;
  * `contracts.manifest.JOB_INPUT_EXCLUDED` deliberately does NOT contain
    `human_contract` -- the task is "which task, by content digest", inside
    `job_input_identity`, which is what `stage_execution._disagreements` and
    `single_worker._claimed` compare.

The third is why the gap cannot be closed by deriving a different Job digest
on its own: a Job whose input identity named the requested task while its
workers' manifests named the installed one is refused for every stage. THE
MANIFEST AND THE TASK IT NAMES MOVE TOGETHER -- which is
`stage_execution._served_deployment`'s own sentence, written for the
integration role and true of this.

SO THIS COMPOSES BOTH, AND IT LIVES IN `tools`. The task document's vocabulary
is `v12/worker/claude_agent.py`'s -- `baton.dogfood-task/2`, exactly
`schema, task_id, instructions, verification, source_root, source_profile,
declared_base` -- and nothing from `baton_v12` travels into that image. A
composer inside the package would put the worker's vocabulary in the manager;
this is the deployment side, where `single_worker` already holds the
`human_contract` rule.

WHAT THIS IS AND IS NOT A READER OF, because `_task_bytes` is explicit that
the host does not parse this document: "`claude_agent` owns that vocabulary at
the receiving end, and a host-side copy of it would be a second reader of one
contract." This is a SUBSTITUTION of two named members and not a second
reader. It decodes the installed bytes, replaces exactly `task_id` and
`instructions` -- the two the caller's request owns -- and re-serializes.
Every other member travels as the deployment wrote it: `verification` is the
deployment's command, `source_root` is a constant of the contract,
`source_profile` and `declared_base` are the source profile's. Nothing else is
interpreted, nothing is defaulted, and the receiving adapter remains the only
party that validates the vocabulary. If a substitution produced a document
that adapter refuses, the adapter is the right owner of that refusal.

AND NO DIGEST CHECK IS WEAKENED ANYWHERE. The composed bytes get their own
`content_digest` and `bytes`, the manifest's `human_contract` is replaced with
that artifact and its `manifest_digest` is RECOMPUTED by §12's own rule, and
`check_manifest_structure` is what proves the result -- so the per-Job
manifest is a manifest that identifies itself, exactly as the installed one
does. `_task_bytes` then holds the delivered bytes to this artifact with the
unchanged comparison it always made.
"""

import json

from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.contracts.errors import name_value
from baton_v12.contracts.manifest import check_manifest_structure

__all__ = ["CONTRACT_MEDIA_TYPE", "MAX_INSTRUCTIONS", "SELECTION_MEMBERS",
           "CALLER_SELECTION", "SUBSTITUTED", "compose_task",
           "delivered_bytes",
           "instructions_for", "manifest_for", "per_job_delivery"]

# The two members a caller's request owns. CLOSED, and deliberately short: a
# third would be this composer deciding something the deployment configured.
SUBSTITUTED = ("task_id", "instructions")

# What the manifest's human-contract artifact must already say it is.
# `single_worker._task_bytes` refuses anything else for this profile, so a
# composed artifact claiming another media type would be one that validator
# would never accept.
CONTRACT_MEDIA_TYPE = "application/json"

# A bound on the instructions this composes. `single_worker.MAX_TASK_BYTES`
# bounds the WHOLE document at its own ceiling and refuses past it; this is the
# narrower bound on the one member composed here, so an over-long statement is
# refused where it is written rather than as a document width somebody has to
# work backwards from.
MAX_INSTRUCTIONS = 16384


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


# What a selection must name for this composition. CLOSED. It is deliberately
# NOT a resolution: the task bytes decide the Job's input identity, the input
# identity is an operand of `templates.resolve`, and a composer that needed a
# resolution to make them could never be called. Every member here is one the
# caller's request owns or the deployment already answered, so all of them
# exist before anything is resolved.
SELECTION_MEMBERS = ("job_id", "work_id", "statement", "acceptance", "scope",
                     "template_version")
# And the ones the CALLER supplies: `work_id` is the deployment's own answer
# and `creation_ports` adds it, so a creation never has to read the
# configuration twice to compose one task.
CALLER_SELECTION = tuple(one for one in SELECTION_MEMBERS
                         if one != "work_id")


def instructions_for(selection):
    """The caller's task, as the one text member the worker reads.

    THE THREE THINGS THE REQUEST OWNS, in one document-shaped order: what the
    task is, what it will be judged against, and which paths it covers. The
    worker reads `instructions` as bounded non-empty text and nothing more --
    `claude_agent` holds it to `type(...) is str and document[name]` -- so the
    structure here is for the HUMAN and the provider reading it, not a second
    schema for a machine to parse.

    AND IT IS DERIVED FROM THE RESOLUTION, never from a caller's free text
    beside it. `templates.resolve` already owned every member of this: the
    statement is bounded, the acceptance criteria are a bounded non-empty
    list, and both scopes are repository-relative deduplicated paths. So this
    renders facts that are already proved rather than accepting prose.
    """
    if type(selection) is not dict:
        _refuse(f"a task selection is one document; this is "
                f"{name_value(selection)}")
    held = {name: selection[name] for name in SELECTION_MEMBERS
            if name in selection}
    missing = [one for one in SELECTION_MEMBERS if one not in held]
    if missing:
        _refuse(f"a task selection names {', '.join(SELECTION_MEMBERS)}; this "
                f"one is missing {', '.join(missing)}")
    extra = sorted(one for one in selection
                   if one not in SELECTION_MEMBERS)
    if extra:
        _refuse(f"a task selection also carries {', '.join(extra)}, which "
                f"this composition does not render; an unrendered member is "
                f"a fact somebody believes reaches the worker")
    # EVERY MEMBER IS OWNED BEFORE IT IS RENDERED. This is a public function
    # in a module a deployment composes, so its operand is receiver input --
    # the R4 lesson one Work over, where a surface that dereferenced before it
    # validated left `TypeError` and `KeyError` at a boundary whose whole job
    # is to refuse. `creation` already owns these shapes before it composes a
    # selection; that is not a reason for this to trust them.
    for name in ("job_id", "statement", "template_version"):
        if type(held[name]) is not str or not held[name]:
            _refuse(f"a task selection's {name} is bounded non-empty text; "
                    f"this is {name_value(held[name])}")
    if type(held["acceptance"]) is not list or not held["acceptance"] \
            or not all(type(one) is str and one
                       for one in held["acceptance"]):
        _refuse(f"a task selection's acceptance is a non-empty list of "
                f"criteria; this is {name_value(held['acceptance'])}. A task "
                f"with nothing to be judged against cannot be independently "
                f"reviewed, which is this template's second stage")
    if type(held["scope"]) is not dict \
            or sorted(held["scope"]) != ["tests", "work"]:
        _refuse(f"a task selection's scope names work and tests; this is "
                f"{name_value(held['scope'])}")
    for member in ("work", "tests"):
        value = held["scope"][member]
        if type(value) is not list \
                or not all(type(one) is str and one for one in value):
            _refuse(f"a task selection's {member} scope is a list of "
                    f"repository-relative paths; this is "
                    f"{name_value(value)}")
    if not held["scope"]["work"]:
        _refuse("a task selection's work scope is non-empty; a task that "
                "covers no path has nothing for a reviewer to read a "
                "proposal against")
    scope = held["scope"]
    lines = [held["statement"], ""]
    lines.append("Acceptance criteria:")
    for one in held["acceptance"]:
        lines.append(f"  - {one}")
    lines.append("")
    lines.append("Selected work scope (the paths this task covers):")
    for one in scope["work"]:
        lines.append(f"  - {one}")
    lines.append("")
    if scope["tests"]:
        lines.append("Bounded test-change scope (tests you may change):")
        for one in scope["tests"]:
            lines.append(f"  - {one}")
    else:
        lines.append("Bounded test-change scope: none. This task changes no "
                     "test.")
    lines.append("")
    lines.append(f"Template: {held['template_version']}")
    lines.append(f"Work: {held['work_id']}")
    rendered = "\n".join(lines) + "\n"
    if len(rendered.encode("utf-8")) > MAX_INSTRUCTIONS:
        _refuse(f"this task's composed instructions are "
                f"{len(rendered.encode('utf-8'))} bytes and this composer "
                f"admits "
                f"{MAX_INSTRUCTIONS}; the statement and the acceptance "
                f"criteria are bounded individually and their rendering is "
                f"bounded here, so a document nobody could deliver is "
                f"refused where it is composed",
                category="refused", code="limit")
    return rendered


def compose_task(installed, *, task_id, instructions):
    """The installed task document with exactly two members substituted.

    `installed` is the bytes `single_worker._task_bytes` read and held. What
    comes back is TEXT, and `delivered_bytes` below is the one place it becomes
    bytes again.

    WHY TEXT RATHER THAN BYTES. The composed document has to travel through
    `creation`'s derivation contract and be stored in the Job store, and both
    of those are `contracts.own` boundaries that refuse `bytes` -- it is not
    JSON data. Text that this module alone encodes is exactly equivalent: the
    encoding is UTF-8 and nothing else ever chooses it, so the artifact digest
    and the delivered bytes are one computation reached from one string.

    SERIALIZED DETERMINISTICALLY, so one intent composes one document. Two
    deliveries of one Job must produce byte-identical bytes or the restart
    comparison `_proved_task` makes is a comparison of two renderings.

    SORTED AND SEPARATED DETERMINISTICALLY, so one intent composes one
    document. Two deliveries of one Job must produce byte-identical bytes or
    the restart comparison `_proved_task` makes is a comparison of two
    renderings.
    """
    if type(installed) is not bytes:
        _refuse(f"an installed task document is bytes; this is "
                f"{name_value(installed)}")
    try:
        held = json.loads(installed.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        _refuse("the installed task document is not readable as one JSON "
                "document, so there is nothing to substitute into")
    if type(held) is not dict:
        _refuse(f"the installed task document is one object; this is "
                f"{name_value(held)}")
    missing = [one for one in SUBSTITUTED if one not in held]
    if missing:
        # NOT A VALIDATION OF THE VOCABULARY. The only members this asks about
        # are the two it replaces: a document that does not carry them is one
        # this substitution cannot be performed on, which is a different
        # statement from "this document is invalid".
        _refuse(f"the installed task document carries no "
                f"{', '.join(missing)}, so this composition has nothing to "
                f"substitute; the members a request owns are "
                f"{', '.join(SUBSTITUTED)} and every other member travels as "
                f"the deployment wrote it",
                category="refused", code="precondition")
    for name, value in (("task_id", task_id), ("instructions", instructions)):
        if type(value) is not str or not value:
            _refuse(f"a composed task's {name} is bounded non-empty text; "
                    f"this is {name_value(value)}")
    held = dict(held, task_id=task_id, instructions=instructions)
    return json.dumps(held, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))


def delivered_bytes(task):
    """The one encoding of a composed task, and the only one anybody uses.

    Every digest over this document and every byte written into an input root
    comes through here, so "the bytes the artifact names" and "the bytes the
    worker reads" cannot be two different renderings of one string.
    """
    if type(task) is not str or not task:
        _refuse(f"a composed task document is non-empty text; this is "
                f"{name_value(task)}")
    return task.encode("utf-8")


def manifest_for(manifest, task):
    """The installed manifest naming THIS Job's task, and identifying itself.

    THE ARTIFACT KEEPS EVERY MEMBER IT HAD EXCEPT THE THREE THAT DESCRIBE THE
    BYTES. `artifact_id` and `locator` are provenance the deployment wrote and
    `_task_bytes` never reads the locator as a host path, so they travel; the
    media type is held to this profile's one value rather than copied, because
    a composed artifact claiming another would be one `_task_bytes` refuses.

    AND THE MANIFEST DIGEST IS RECOMPUTED, by §12's rule -- the digest over the
    document without that member -- then the whole thing is proved by
    `check_manifest_structure`, which is `verify_manifest_digest` plus the §12
    semantics plus the secret sweep. A per-Job manifest that did not identify
    itself would be refused by every reader downstream, which is correct and
    is not something to discover there.
    """
    if type(manifest) is not dict or "human_contract" not in manifest:
        _refuse("an installed input manifest carries a human contract; this "
                "one does not, so there is no task artifact to replace")
    contract = manifest["human_contract"]
    if type(contract) is not dict:
        _refuse(f"an installed manifest's human contract is one artifact; "
                f"this is {name_value(contract)}")
    if contract.get("media_type") != CONTRACT_MEDIA_TYPE:
        _refuse(f"this profile's task document is the input manifest's human "
                f"contract and that artifact is "
                f"{name_value(contract.get('media_type'))} rather than "
                f"{name_value(CONTRACT_MEDIA_TYPE)}; a composed task cannot "
                f"claim a media type the delivery would refuse",
                category="refused", code="precondition")
    raw = delivered_bytes(task)
    held = dict(manifest)
    held["human_contract"] = dict(contract, bytes=len(raw),
                                  content_digest=digest_of_bytes(raw))
    held["manifest_digest"] = digest(
        {name: value for name, value in held.items()
         if name != "manifest_digest"})
    # PROVED BY ITS OWN OWNER before anybody is handed it.
    return check_manifest_structure(held, "inputManifest",
                                    what="a created Job's input manifest")


def per_job_delivery(installed_task, installed_manifest, selection):
    """One created Job's task bytes and the manifest that names them.

    THE TWO TOGETHER, in one call, because they are one fact and the product
    already says so: `_served_deployment`'s comment reads "a derived document
    carrying this Job's manifest beside another Job's task bytes would be one
    that validator would never have accepted". A composer with two entry
    points is two chances to deliver half of it.
    """
    # THE INSTRUCTIONS FIRST, because `instructions_for` is what OWNS the
    # selection -- reading `selection["job_id"]` before it left a `KeyError`
    # for a selection missing that member, which is the same
    # dereference-before-validate shape R4 corrected one Work over.
    instructions = instructions_for(selection)
    task = compose_task(installed_task, task_id=selection["job_id"],
                        instructions=instructions)
    return {"task_document": task,
            "input_manifest": manifest_for(installed_manifest, task)}
