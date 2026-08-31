"""W39358 — the minimal supervised dogfood operator.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-minimal-supervised-operator/`.

WHAT THIS IS. One documented composition of capabilities other Work already
delivered and other Work already reviewed: the accepted Worker Manager
lifecycle (W6636), the Docker worker-entry transport (W39356) and the real
Claude worker image (W39357). It is a DEPLOYMENT, and the whole of its value
is that it is the only place where those three meet.

WHAT IT IS EMPHATICALLY NOT, and each line is a boundary somebody could
reasonably have crossed:

  NOT A SECOND MANAGER. Every durable decision here goes through a public
  `baton_v12.worker_manager` operation. This module journals nothing, opens no
  control store table, recomputes no signature and invents no state. If a
  question can only be answered by reaching past those operations, that
  inability is the finding.
  NOT AN AUTHORITY. `DeploymentSession` is a FACADE over one already-minted
  `baton_v12.authority.Session`; it mints nothing and widens nothing.
  NOT A MERGE TOOL. It derives the candidate's diff and the task's own
  verification result INDEPENDENTLY, and it never stages, merges, or writes
  into the canonical checkout. What it produces is a proposal an operator
  reads.
  NOT AN AUTHORIZATION. Every grant is an explicit operand: the exact source
  subset, the frozen task, the image DIGEST, the engine, the manager's own
  roots, the configured workspace group, the credential source and the network
  name. There is no home credential, no mutable image tag and no open-network
  default anywhere in this file, because a default is a grant nobody made.

THE ORDER, and it is the accepted arc rather than this module's invention:

  1. offer, accept, record, claim, activate       -- the authority half
  2. workspace roots, input root, staged source   -- the delivery half
  3. launch document, credential delivery         -- the two manager roots
  4. runtime start, worker-entry conversation     -- the one container
  5. freeze, intake, retention                    -- output custody
  6. pass the assignment to its review route      -- the v11 lifecycle
  7. destroy, positive absence, teardown          -- the ending

THE COMMAND, and it is one because the acceptance asks for one that is
REUSABLE for another bounded task:

    python3 tools/dogfood_operator.py --grants GRANTS.json \
        --evidence OUT.json [--credential-file PATH] [--retry-handoff]

`--credential-file` names the provider credential this attempt delivers. It is
read once into memory and never written back, and it is deliberately NOT a
grants member: a grants file is a durable surface and §13 keeps the one
deliberate secret off every one of them. The path is not the secret.

`retention_disposition` is one of the manager's frozen three -- `retain`,
`quarantine` or `discard-after-intake` -- and it decides whether this attempt
leaves its candidate behind. It has no default and is not derived from
`retention_policy_digest`: W39364's first live attempt ran the whole arc under
a HARD-CODED discard and destroyed the proposal it existed to produce,
including the worker's own account of why it answered `unable`. A `retain` or
`quarantine` run ends `retained` rather than `complete` -- that is the
manager's own vocabulary for "the material is still there" -- and this command
reports it resolved, having proved the custody locator is still openable.

`--retry-handoff` performs approver ruling M46985's narrow retry over the
record in `--evidence`: an attempt whose worker COMPLETED, whose output was
frozen and whose candidate this operator independently verified, but whose
pass or settlement then failed. It runs no worker, starts no runtime, opens no
provider turn and restages nothing -- it redoes the pass and the ending, both
under the original identities, so the authority and the manager replay rather
than repeat.

`GRANTS.json` is the whole of what an operator decides. Nothing in it has a
default and nothing is read from the environment, because a grant nobody made
is the failure this deployment exists to avoid:

    {
      "engine": "docker",
      "attempt_id": "...", "offer_id": "...",
      "source": "/abs/path/to/the/exact/subset",
      "task_path": "/abs/path/to/task.json",
      "storage": "/abs/path/manager-storage",
      "launch_home": "/abs/path/launch-home",
      "control_store": "/abs/path/control.sqlite3",
      "authority_store": "/abs/path/authority.sqlite3",
      "incarnation": "dogfood-1",
      "credential_home": "/abs/path/credential-home",
      "credential_slots": [...the slots this assignment authorizes...],
      "credential_profile": {...the trusted slot-to-provider mapping...},
      "image_digest": "sha256:...", "network": "baton-dogfood",
      "review_route": "rview",
      "retention_disposition": "retain",
      "retention_policy_digest": "sha256:...",
      "work_ref": {"authority_uuid": "...", "work_id": "..."},
      "participant": "team.member", "generation": 1,
      "now": "2026-08-30T00:00:00.000Z",
      "policies": {...the seven policy identities...},
      "record_binding": {...root, path and the two digests...},
      "assignment_contract": "...", "human_contract": {...},
      "role_instructions_digest": "sha256:...",
      "runtime_profile_digest": "sha256:...",
      "toolchain_digest": "sha256:...",
      "adapter_digest": "sha256:...", "adapter_name": "oci",
      "labels": {...}, "retention_policy_digest": "sha256:..."
    }

REUSING IT FOR ANOTHER BOUNDED TASK is changing `task_path`, `source` and the
identities -- and nothing in this file. That is the whole claim: the arc is
the same arc, and what varies is what an operator granted.

TWO THINGS THE COMMAND DELIBERATELY DOES NOT TAKE. The one-use bearer and the
authority session are supplied by the launcher through
`compose(...)`/`main(...)` operands rather than read from a file or an
environment variable, because §13 keeps the one deliberate secret off every
durable surface and a grants file is a durable surface.

WHAT AN UNRESOLVED ATTEMPT IS. Whenever runtime absence, output custody or
credential cleanup cannot be PROVED, this reports `unresolved` and says which
proof is missing. It never relabels an unproved ending as a clean one -- that
is the one failure mode a supervised pilot must not have, because the operator
reading the evidence is deciding whether to run another.
"""

import json
import os
import re

from baton_v12.contracts import ContractRefusal, check_no_durable_secret
from baton_v12.contracts import validate_fragment as _validate_fragment
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.oci import _network as _engine_network
from baton_v12.worker_manager.authority_port import SESSION_OPERATIONS

__all__ = ["DeploymentSession", "MAX_SOURCE_ENTRIES", "MAX_SOURCE_BYTES",
           "PROPOSAL_TARGET", "POLICY_DIGESTS", "SOURCE_TARGET",
           "OperatorRefusal", "assignment_manifest", "frozen_task",
           "held_task", "input_manifest", "preflight", "stage_source"]


# WHERE THE STAGED SOURCE LANDS INSIDE THE INPUT ROOT, and it is fixed for the
# reason every other path in this campaign is: a path a payload can vary is a
# path a runtime can be pointed at wrongly. `claude_agent.SOURCE_ROOT` is the
# other half of this agreement and holds the same constant by equality.
SOURCE_TARGET = "source"

# WHERE THE PROPOSAL LANDS, relative to the fixed `/output` root. The parent
# finding's accepted tree is `/output/proposal/`, and W39357's adapter joins
# the declared path directly below `/output` -- so this is the same constant
# seen from the two ends of one agreement.
PROPOSAL_TARGET = "proposal"

# WHAT A DIGEST LOOKS LIKE. Held on the way in because every policy identity
# this deployment names is one it is accountable for, and "sha256:" plus 64
# hex is what the manager compares.
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")

# WHAT THE OPERATOR MAY STAGE, bounded on both axes at the party that walks
# it. The manager bounds its own roots; this is the second bound, at the one
# place a human names a directory.
MAX_SOURCE_ENTRIES = 2000
MAX_SOURCE_BYTES = 64 * 1024 * 1024


class OperatorRefusal(Exception):
    """Something this operator will not proceed from.

    Deliberately not a `ContractRefusal`: those are the manager's judgements
    about its own contracts, and this one is a deployment saying it was asked
    for something it does not do. Conflating them would let an operator
    mistake a composition mistake for a protocol refusal.
    """


class DeploymentSession:
    """The authority face this deployment gives the manager, and no more.

    SIX MEMBERS DELEGATE, one refuses, and ONE MORE IS THIS DEPLOYMENT'S OWN.
    `AuthorityPort` names exactly seven session operations and checks all of
    them are callable at construction, so a facade that simply omitted
    `publish_answer` would be refused before the first offer -- and one that
    quietly forwarded it would be promising a Baton publication this pilot
    does not perform.

    `pass_work` IS THE EIGHTH AND IT IS NOT THE MANAGER'S. Approver ruling
    M44657: the v11 lifecycle is preserved in v12, so after intake,
    independent verification and retention this deployment explicitly passes
    the exact assignment generation to an operator-supplied review Route. The
    manager's port does not name that operation and this deployment does not
    ask it to -- the port checks the seven it names and ignores anything else,
    so the capability lives where the ruling put it: on the deployment's own
    facade, over the deployment's own already-minted session.

    WHY `publish_answer` IS A TYPED REFUSAL RATHER THAN A NO-OP. It is the
    manager's route for a conversational `inquire` answer, and this pilot runs
    no `inquire` at all. A no-op would answer "published" to something nobody
    published; a refusal says the deployment does not carry that capability,
    which is true and is what an operator needs to read.

    IT MINTS NOTHING. What it holds is one already-minted participant-bound
    `Session`; there is no route from here to a second one, which is the
    property the authority's own mint rule exists to give.
    """

    def __init__(self, session):
        # THE EIGHTH IS CHECKED WITH THE SIX, because it is delegated like
        # them. Review 2026-08-30T12:27:41Z [P1]: only the port's operations
        # were held, so this facade's own `pass_work` was callable over a
        # session that had none -- and `run_dogfood_task`'s preflight, which
        # asks the FACADE, was satisfied by the very method that would fail.
        # A capability check that inspects the wrapper rather than the thing
        # wrapped is not a check, and the discovery moved to after staging, a
        # container, a conversation, intake and retention.
        for member in SESSION_OPERATIONS + ("pass_work",):
            if member == "publish_answer":
                continue
            if not callable(getattr(session, member, None)):
                raise OperatorRefusal(
                    f"the authority session this deployment was given has no "
                    f"callable {member}; a facade cannot supply an operation "
                    f"the session it delegates to does not have")
        self._session = session

    @property
    def participant(self):
        """The bound identity, read from the session rather than configured."""
        return self._session.participant

    def project_work(self, *arguments):
        return self._session.project_work(*arguments)

    def slot_holder(self, *arguments):
        return self._session.slot_holder(*arguments)

    def claim(self, *documents):
        return self._session.claim(*documents)

    def settle_operation(self, *documents):
        return self._session.settle_operation(*documents)

    def assignment_of(self, *arguments):
        return self._session.assignment_of(*arguments)

    def cancel(self, *documents):
        return self._session.cancel(*documents)

    def pass_work(self, *documents):
        """Hand the exact assignment generation to its review Route.

        Delegated rather than composed, like every other member here: the
        authority owns what a pass MEANS -- it moves the Route and ends the
        assignment in one act -- and a facade that reimplemented any part of
        that would be a second spelling of the transition.
        """
        return self._session.pass_work(*documents)

    def publish_answer(self, *documents):
        """The one member this deployment does not carry."""
        raise OperatorRefusal(
            "this dogfood deployment publishes no conversational answer: it "
            "runs no `inquire`, so there is no answer to publish and a "
            "successful-looking no-op would be a publication nobody made")


def held_human_contract(document, *, what="the human contract"):
    """ONE human-contract hold, applied everywhere the contract is believed.

    W51476, and it is `held_task`'s defect one grant over. `preflight` held
    the policies, the record binding, the network, the review route and the
    task; `input_manifest` then copied `human_contract` into the frozen
    document and left it to `check_input_pair`. So the grant was validated
    for the first time by the WHOLE-MANIFEST validator -- which
    `compose_input_root` runs after `stage_source` has written the delivery,
    after `submit_claim`, after `activate_assignment` and after the credential
    home has materialized the attempt's slot.

    W39364's first live invocation is what found it. A locator of
    `baton:work/records/...` -- the ordinary opaque spelling -- passed
    everything an operator could check and was refused halfway through an
    attempt that had already taken a claim and an activation. No runtime and
    no provider turn started, so nothing unsafe happened; what happened is
    that the no-side-effect interval `preflight` documents was open.

    TWO GRAMMARS, BOTH IMPORTED, AND THE NARROWER ONE IS THE REAL CONTRACT.
    `artifactRef` is the frozen `$defs` shape and its `locator` pattern admits
    `scheme:anything`; `contracts.manifest.check_uri` is what the manifest
    actually applies, and it requires `scheme://` followed by an authority --
    EXCEPT for `file:`, which has its own form, `file:///` and an absolute
    path with no host, because a file locator naming a host would be a claim
    about somebody else's filesystem. Review 2026-08-31T05:27:01Z asked for
    that precision and it is worth having: the positive cases use both forms.
    Applying the loose grammar alone is what let the two lifecycle times
    disagree, so this applies BOTH -- the shape from the schema, then the
    locator from the manifest's own owner. Neither is rewritten here: a third
    spelling would be a third thing to disagree with.

    ONE FUNCTION, TWO CALL SITES, for the reason `held_task` gives in its own
    words: checking a document twice with two different rules is not the same
    hold. This runs at the preflight and again immediately before the manifest
    is composed from it, so a contract that was read valid and then changed is
    not the contract that gets frozen.
    """
    from baton_v12.contracts import check_uri

    if type(document) is not dict:
        raise OperatorRefusal(f"{what} is one JSON object; this is a "
                              f"{type(document).__name__}")
    # THE FROZEN SHAPE FIRST, from the schema that owns it. Every member, its
    # type, the media-type grammar, the digest and the byte bound come from
    # `artifactRef` rather than from a list maintained here.
    try:
        _validate_fragment(document, "artifactRef", what=what)
    except ContractRefusal as refused:
        # THE CONTRACT'S OWN SENTENCE, as the record binding's locators
        # already do: the refusal text says which rule the value broke, and a
        # class name would send an operator reading this file instead of
        # their own document.
        raise OperatorRefusal(f"{what} is not an artifact reference: "
                              f"{refused.message}") from None
    # AND THEN THE LOCATOR, BY THE GRAMMAR THE MANIFEST WILL APPLY. This is
    # the whole finding: `artifactRef` admits `baton:<path>` and
    # `check_input_pair` does not, so the operand has to meet the stricter of
    # the two here, where refusing it costs nothing.
    try:
        check_uri(document["locator"], f"{what} locator")
    except ContractRefusal as refused:
        raise OperatorRefusal(f"{what} locator is not one the frozen input "
                              f"manifest will accept: {refused.message}") \
            from None
    return dict(document)


def held_disposition(disposition):
    """The retention disposition an operator chose, held to the MANAGER's own
    vocabulary.

    W51473. The first live attempt (W39364 `attempt-w39364-run2`) completed the
    whole arc and then destroyed the thing it existed to produce: `_custody`
    passed the literal `"discard-after-intake"` to `decide_retention`, so the
    `retention_policy_digest` an operator granted named a policy whose
    DISPOSITION nothing read. The manager took custody of an 86,417-byte
    proposal, this operator derived it, and the discard then removed the
    tree -- taking `result.json`, the worker's own bounded account of its
    `unable` answer, and the candidate a human is required to inspect. The
    sealed result's own locator named a directory that no longer existed.

    A LITERAL IS NOT A DECISION, and that is the whole finding. Retention
    decides whether a supervised attempt leaves anything behind, which is the
    most consequential thing about a supervised attempt; it is an operator
    grant like the network and the credential source, with no default and
    nothing derived from the policy digest.

    ONE VOCABULARY, IMPORTED. `schema.RETENTION_DISPOSITIONS` is the manager's
    frozen three and `intake._disposition` is the rule that enforces them; a
    second tuple spelled here would be a second vocabulary that agrees until
    one of the two is edited. This holds the operand to the imported set and
    says which three, so an operator reads the answer rather than this file.
    """
    from baton_v12.worker_manager import RETENTION_DISPOSITIONS

    if type(disposition) is not str \
            or disposition not in RETENTION_DISPOSITIONS:
        raise OperatorRefusal(
            f"the retention disposition is one of the manager's frozen three "
            f"-- {', '.join(RETENTION_DISPOSITIONS)} -- named explicitly; "
            f"this is {disposition!r}. Retention decides whether this attempt "
            f"leaves its candidate behind for review, so it is granted like "
            f"the network and the credential source and is never defaulted "
            f"or derived from the policy digest")
    return disposition


# WHICH DISPOSITIONS MEAN THE MATERIAL STAYS -- the manager's own answer,
# imported for the same reason `held_disposition` imports the vocabulary.
# `intake.KEEPS_MATERIAL` is what makes cleanup end `retained` rather than
# `complete`, so a deployment deciding whether a `retained` ending is the one
# it asked for has to be reading that exact tuple.
def _keeps_material(disposition):
    from baton_v12.worker_manager.intake import KEEPS_MATERIAL

    return disposition in KEEPS_MATERIAL


def preflight(*, task, policies, worker_image_digest, toolchain_digest,
              runtime_profile_digest, role_instructions_digest,
              record_binding, network, review_route, retention_disposition,
              human_contract):
    """EVERY EXPLICIT OPERAND, HELD BEFORE ANYTHING IS STAGED OR STARTED.

    Review 2026-08-30T05:53:19Z [P1]. The first round put the policy check
    inside `input_manifest`, which takes the already-produced staged manifest
    -- so the record claimed a refusal happened "while nothing has been
    staged" and the code could not deliver it. **Superseded:** that claim.
    This is the pure preflight it described, and it runs before
    `stage_source` writes anything.

    IT HOLDS VALUES AND NOT ONLY KEYS, which was the other half of the
    finding. `policy_digest="not-a-digest"` passed a key check and was left
    for the manager to refuse after the delivery existed; every digest operand
    is held to its shape here.

    IT DOES NOT VALIDATE THE TASK'S CONTENT, only that it is a task this
    deployment reads -- `frozen_task` owns that and is called with the
    operator's path. What this adds is that the task is checked in the same
    act as everything else, so one refusal reports the whole preflight rather
    than one operand at a time.
    """
    faults = _held_identities(
        policies=policies, worker_image_digest=worker_image_digest,
        toolchain_digest=toolchain_digest,
        runtime_profile_digest=runtime_profile_digest,
        role_instructions_digest=role_instructions_digest,
        record_binding=record_binding)
    # THE NETWORK IS A NAME AND NEVER A DEFAULT, and it is held to the
    # ENGINE'S OWN GRAMMAR rather than to a second one written here. Review
    # 2026-08-30T06:05:02Z [P1]: any non-empty string passed, including
    # `--network=host`, `../bridge` and `two words`, and `oci._network`
    # refused them only when the runtime vector was composed. Reusing that
    # owner is what keeps the operator and the adapter from drifting.
    try:
        _engine_network(network)
    except ContractRefusal:
        # EXACTLY THE TYPED OUTCOME, and nothing else. Review
        # 2026-08-30T06:20:54Z [P2]: `except Exception` here turned an
        # implementation defect in the owner into an `OperatorRefusal`, which
        # tells a human to edit a grant that is fine and hides the boundary
        # that actually failed. `OperatorRefusal`'s own docstring draws that
        # distinction; catching broadly erased it.
        faults.append("the engine network is one engine network name, named "
                      "explicitly")
    # THE REVIEW ROUTE IS NAMED, NEVER DEFAULTED. Approver ruling M44657 makes
    # the pass part of the arc, and where the Work goes next is a DEPLOYMENT
    # decision -- so it is an operand held here beside the network, and an
    # operator who did not say gets a refusal rather than somebody's guess at
    # a sensible destination.
    if type(review_route) is not str or not review_route.strip():
        faults.append("the review route this attempt is passed to is one "
                      "non-empty name, named explicitly")
    # AND THE RETENTION DISPOSITION, held here beside the network and the
    # review route because it is the same kind of grant: a deployment decision
    # with no default, whose absence is a refusal rather than somebody's guess.
    # W51473: it used to be a literal inside `_custody`, so the operator asked
    # for a discard on every run and no operator could say otherwise.
    try:
        held_disposition(retention_disposition)
    except OperatorRefusal as refused:
        faults.append(str(refused))
    # THE WHOLE TASK, not its schema. See `held_task`.
    try:
        held_task(task)
    except OperatorRefusal as refused:
        faults.append(str(refused))
    # AND THE WHOLE HUMAN CONTRACT, for exactly the same reason and by the
    # same shape of owner. W51476: this grant reached the frozen manifest
    # unvalidated and was refused there -- after the delivery, the claim, the
    # activation and the credential slot existed.
    try:
        held_human_contract(human_contract)
    except OperatorRefusal as refused:
        faults.append(str(refused))
    if faults:
        raise OperatorRefusal(
            "this operator will not stage or start anything until every "
            "grant it was given is one it can name: " + "; ".join(faults))
    return True


def _held_identities(*, policies, worker_image_digest, toolchain_digest,
                     runtime_profile_digest, role_instructions_digest,
                     record_binding):
    """The digest and record-binding half of the preflight, as a fault list.

    Split out so `input_manifest` can apply the same hold at the composer
    without being handed a task it does not have. One owner, two callers, and
    no second spelling of what a policy identity is.
    """
    faults = []
    # THE CONTAINER BEFORE ITS CONTENTS. Review 2026-08-30T06:05:02Z [P1]:
    # `policies=None` leaked `TypeError` and a string leaked `ValueError`, so
    # the public promise of one collected `OperatorRefusal` over explicit
    # grants was false for exactly the operands most likely to arrive wrong.
    if type(policies) is not dict:
        raise OperatorRefusal(
            f"the policy identities are one document naming "
            f"{', '.join(POLICY_DIGESTS)}; this is a "
            f"{type(policies).__name__}")
    missing = sorted(one for one in POLICY_DIGESTS if one not in policies)
    extra = sorted(one for one in policies if one not in POLICY_DIGESTS)
    if missing or extra:
        faults.append(
            "the policy identities are exactly "
            + ", ".join(POLICY_DIGESTS)
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    named = dict(policies)
    named.update({"worker_image_digest": worker_image_digest,
                  "toolchain_digest": toolchain_digest,
                  "runtime_profile_digest": runtime_profile_digest,
                  "role_instructions_digest": role_instructions_digest})
    for name in sorted(named):
        value = named[name]
        if type(value) is not str or not _DIGEST.match(value):
            faults.append(f"{name} is not a sha256 digest")
    # THE RECORD BINDING'S VALUES, not only its four names. Review
    # 2026-08-30T06:05:02Z [P1]: four correctly named members passed with a
    # malformed digest, an empty root or an absolute path, and the frozen
    # input-manifest schema refused them only after the source was staged.
    if type(record_binding) is not dict \
            or sorted(record_binding) != sorted(_RECORD_BINDING):
        faults.append("the record binding is exactly "
                      + ", ".join(_RECORD_BINDING))
    else:
        for name in ("finding_digest", "plan_digest"):
            value = record_binding[name]
            if type(value) is not str or not _DIGEST.match(value):
                faults.append(f"the record binding's {name} is not a sha256 "
                              f"digest")
        # THE FROZEN CONTRACT'S OWN GRAMMAR, through its own owner. Review
        # 2026-08-30T06:13:35Z [P1]: the previous cut wrote an approximation
        # here -- any non-empty string as the root, `posixpath.normpath` plus
        # a few exclusions as the path -- so a root with spaces or 161
        # characters, and a path of `.`, with a backslash, with a NUL or 513
        # characters long, all reached `_sealed`, which refused them AFTER
        # `stage_source` had created the delivery. That is exactly the
        # interval this preflight exists to remove, and the record's claim
        # that both locators were held by value was stronger than the code.
        #
        # `validate_fragment` is the frozen document's own `$defs` owner, and
        # reusing it is the same rule the network operand is under: a second
        # approximation maintained here is a second grammar with nothing
        # comparing the two.
        for name, definition in (("root", "opaqueId"),
                                 ("path", "relativePath")):
            try:
                _validate_fragment(record_binding[name], definition,
                                   what=f"the record binding's {name}")
            except ContractRefusal as refused:
                # THE CONTRACT'S OWN SENTENCE, not a summary of it. The
                # refusal text is composed by the frozen validator and says
                # which rule the value broke, which is what an operator needs
                # to fix a launch; a class name would send them reading this
                # file instead of their own document.
                #
                # AND ONLY THE TYPED OUTCOME REACHES IT. Review
                # 2026-08-30T06:20:54Z [P2]: `except Exception` relabelled an
                # owner's implementation defect as a malformed grant, which is
                # the one thing `OperatorRefusal` is documented not to be.
                faults.append(f"the record binding's {name} is not a "
                              f"{definition}: {refused.message}")
    return faults


_RECORD_BINDING = ("root", "path", "finding_digest", "plan_digest")


def stage_source(source, inputs, *, max_entries=MAX_SOURCE_ENTRIES,
                 max_bytes=MAX_SOURCE_BYTES):
    """The exact source subset, copied into the input root, bounded.

    THROUGH THE MANAGER'S OWN COPIER. `workspaces.copied_manifest` is the
    reviewed bounded no-follow path -- it refuses a link at any depth, counts
    what it walks and answers a manifest of what it copied. Writing a second
    copier here would be a second party deciding what a delivery is, which is
    the first defect this campaign found.

    STAGED INTO THE INPUT ROOT AND NOWHERE ELSE. The input root is mounted
    read-only at `/input`, so the worker sees `/input/source` and cannot write
    to it; the adapter copies it into container-private scratch before the
    provider touches anything.
    """
    # THE OPERATOR CONSTANTS ARE A CEILING, not a default. Review
    # 2026-08-30T05:53:19Z [P1]: these were forwarded unchanged, so a caller
    # could widen the bound this module states -- which makes a stated bound
    # a suggestion. A LOWER value is still accepted, because a test or a
    # cautious operator narrowing its own delivery takes nothing away.
    # A NARROWED CEILING IS STILL A CEILING. Review 2026-08-30T06:05:02Z [P2]:
    # this accepted booleans and zero and leaked `TypeError` for text, and one
    # boolean reached `copied_manifest` and surfaced in a manager refusal as a
    # limit of `True` files. Positive exact integers, by the manager's own rule
    # for every other seconds-or-count operand.
    for name, value in (("max_entries", max_entries),
                        ("max_bytes", max_bytes)):
        if type(value) is not int or type(value) is bool or not 0 < value:
            raise OperatorRefusal(
                f"{name} is a positive whole number; this is "
                f"{type(value).__name__} {value!r}")
    if max_entries > MAX_SOURCE_ENTRIES or max_bytes > MAX_SOURCE_BYTES:
        raise OperatorRefusal(
            f"this operator stages at most {MAX_SOURCE_ENTRIES} entries and "
            f"{MAX_SOURCE_BYTES} bytes; a caller may narrow that and may not "
            f"widen it, because a bound a caller can raise is not one this "
            f"module states")
    place = os.path.join(inputs, SOURCE_TARGET)
    if os.path.exists(place):
        raise OperatorRefusal(
            f"{place} already exists; an attempt stages its source once, and "
            f"a second staging into a live input root would be replacing a "
            f"delivery the manager has already measured")
    return workspaces.copied_manifest(source, place, max_entries=max_entries,
                                      max_bytes=max_bytes)


def frozen_task(place):
    """The operator's frozen task document, read and held to its own shape.

    READ HERE AND VALIDATED HERE rather than passed through. The adapter holds
    it to `baton.dogfood-task/1` inside the container, and this reads it on the
    way in so an operator learns about a malformed task before a container
    starts rather than from a failed attempt's evidence.

    IT IS THE OPERATOR'S DOCUMENT. This module does not compose one, because
    a task an operator did not write is a task nobody chose.
    """
    try:
        with open(place, "rb") as reading:
            raw = reading.read(1 << 20)
    except OSError as failed:
        raise OperatorRefusal(
            f"this operator has no readable frozen task at {place} "
            f"({type(failed).__name__}); the task is the operator's own "
            f"document and is named explicitly") from None
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise OperatorRefusal(f"{place} is not a readable document") from None
    return held_task(document, what=place)


def held_task(document, *, what="the frozen task"):
    """ONE task hold, applied everywhere a task is believed.

    Review 2026-08-30T06:05:02Z [P1]. `frozen_task` answered an ordinary
    mutable dict, `preflight` re-checked only its `schema`, and `_copied_task`
    serialized whatever it was handed -- so a task could be read valid, have
    its identity, instructions, verification vector or source root changed,
    pass preflight and be copied into `/input/task.json` as the changed thing.
    **Checking the schema a second time is not the same hold**, which is the
    review's own sentence and the reason this function exists.

    So there is one hold and it is applied at every place a task is believed:
    the first read, the preflight, and immediately before the copy. It is a
    pure function over a document, which is what lets it be applied three
    times without three chances to disagree.

    THE SAME CHECKS THE WORKER MAKES. `claude_agent._task` holds the identity
    grammar, the non-empty text and the non-empty list of words inside the
    container; an operator read that accepted what the container rejects would
    move the promised refusal back to the failed provider attempt it exists to
    avoid.
    """
    if type(document) is not dict:
        raise OperatorRefusal(f"{what} is one JSON object")
    missing = sorted(one for one in _TASK_MEMBERS if one not in document)
    extra = sorted(one for one in document if one not in _TASK_MEMBERS)
    if missing or extra:
        raise OperatorRefusal(
            f"{what} is exactly {', '.join(_TASK_MEMBERS)}"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if document["schema"] != _TASK_SCHEMA:
        raise OperatorRefusal(
            f"{what} says it is {document['schema']!r} and this deployment "
            f"stages {_TASK_SCHEMA!r}")
    if type(document["task_id"]) is not str \
            or not _TASK_ID.match(document["task_id"]):
        raise OperatorRefusal(f"{what} carries no usable task identity")
    for name in ("instructions", "source_root"):
        if type(document[name]) is not str or not document[name]:
            raise OperatorRefusal(
                f"{what} carries a {name} that is not bounded non-empty text")
    verification = document["verification"]
    if type(verification) is not list or not verification \
            or not all(type(one) is str and one for one in verification):
        raise OperatorRefusal(
            f"{what} carries a verification that is a non-empty list of "
            f"words; a command anybody has to assemble from a string is a "
            f"shell, and there is no shell in the worker")
    if document["source_root"] != SOURCE_TARGET:
        raise OperatorRefusal(
            f"{what} names source_root {document['source_root']!r} and this "
            f"deployment stages exactly {SOURCE_TARGET!r}")
    return document


# THE FROZEN TASK'S CONTRACT, and it is W39357's rather than this module's.
# Held here by equality so a document from another generation is refused on
# the way in; `v12/worker/claude_agent.py` holds the same closed set at the
# receiving end, which is the both-ends rule this campaign applies to every
# crossing.
_TASK_SCHEMA = "baton.dogfood-task/1"
_TASK_MEMBERS = ("schema", "task_id", "instructions", "verification",
                 "source_root")
_TASK_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\Z")


def _copied_task(document, inputs):
    """The frozen task, delivered beside the staged source.

    Written by this operator rather than by the manager, for the reason the
    parent finding gives: the task is a WORKLOAD convention and not
    worker-control protocol vocabulary, so the manager neither reads it nor
    carries it in its documents.
    """
    # HELD IMMEDIATELY BEFORE THE WRITE. Review 2026-08-30T06:05:02Z [P1]:
    # this serialized whatever it was handed, so a task read valid earlier and
    # changed afterwards was copied as the changed thing. The hold is the same
    # one `frozen_task` and `preflight` apply -- one function, three places, no
    # chance for three answers.
    document = held_task(document, what="the task being staged")
    place = os.path.join(inputs, "task.json")
    with open(place, "w", encoding="utf-8") as writing:
        json.dump(document, writing, sort_keys=True)
    os.chmod(place, 0o444)
    return place


POLICY_DIGESTS = ("policy_digest", "resource_policy_digest",
                  "network_policy_digest", "mount_policy_digest",
                  "tool_policy_digest", "credential_policy_digest",
                  "retention_policy_digest")


def input_manifest(*, work_ref, staged, created_at, manifest_id,
                   assignment_contract, human_contract, record_binding,
                   role_instructions_digest, runtime_profile_digest,
                   toolchain_digest, worker_image_digest, policies):
    """The manager-authored input manifest for one dogfood attempt.

    COMPOSED HERE BECAUSE THE MANAGER DOES NOT COMPOSE IT. `compose_input_root`
    takes both protocol documents as operands, so the party that knows what
    this delivery IS -- the deployment -- authors them, and the manager holds
    the root against what it was handed.

    EVERY POLICY IDENTITY IS AN OPERAND. The frozen schema requires seven of
    them plus the toolchain, the image and the record binding, and each names
    something the deployment is accountable for. A tool that filled one in
    would be making a grant on an operator's behalf, which is the one thing
    the parent finding forbids this composition to do.

    THE `sources` ENTRY DESCRIBES THE STAGED TREE and its `content_manifest`
    is the one `copied_manifest` answered, not a second measurement. A
    deployment that measured the tree twice would be two parties disagreeing
    about one delivery, which is the defect the manager's own copier exists to
    prevent.

    BOTH PATHS ARE RELATIVE TO A FIXED ROOT, and the first round got both
    wrong. `destination` is below `/input` and `path` is below `/output` --
    `contracts/manifest.py` says so where it checks their overlap, W39357's
    adapter reads `/input/source` and joins the declared output path directly
    below `/output`, and the parent finding's accepted proposal is at
    `/output/proposal`. The first cut wrote `workspace/source` and
    `workspace/proposal`, copied from a conformance vector, which described a
    delivery at `/input/workspace/source` that nothing makes and asked the
    worker to write somewhere nobody collects.

    **Superseded:** the first round's claim that `sources[].destination` is
    "consumed by nothing". It is not a materialization instruction in this
    build -- nothing copies a source to it -- but the MANIFEST RULES read it,
    and it is the durable description of the staged delivery. Filling it
    truthfully matters for that reason rather than merely for tidiness.

    THE FROZEN TASK'S IDENTITY IS NOT IN HERE, and that is the schema's ruling
    rather than a preference. `baton.worker-manifest/input` is closed and
    carries no task member; the task is a WORKLOAD convention that travels in
    `/input/task.json`, the same boundary the parent finding draws for Git. A
    first cut of this function added `task_id` and `compose_input_root` refused
    the document -- recorded because a reader will wonder where the task went.
    """
    # THE SAME HOLD, AGAIN, AT THE COMPOSER. `preflight` is where an operator
    # learns about a bad grant before anything is staged; this is the second
    # party proving it rather than assuming the first did, which is the rule
    # the manager applies to its own roots.
    faults = _held_identities(
        policies=policies, worker_image_digest=worker_image_digest,
        toolchain_digest=toolchain_digest,
        runtime_profile_digest=runtime_profile_digest,
        role_instructions_digest=role_instructions_digest,
        record_binding=record_binding)
    if faults:
        raise OperatorRefusal(
            "an input manifest carries identities this deployment named: "
            + "; ".join(faults))
    return _sealed({
        "version": {"major": 1, "minor": 0},
        "manifest_id": manifest_id,
        "created_at": created_at,
        "extensions": {},
        "schema": "baton.worker-manifest/input",
        "work_ref": dict(work_ref),
        "assignment_contract": assignment_contract,
        # THE SAME HOLD, THE SECOND TIME. `held_task`'s rule: a document
        # read valid at the preflight and changed afterwards is not the
        # document that gets frozen, so the hold is applied here too
        # rather than the value being copied.
        "human_contract": held_human_contract(human_contract),
        "record_binding": dict(record_binding),
        "sources": [{"name": SOURCE_TARGET,
                     "destination": SOURCE_TARGET,
                     "required": True,
                     "content_manifest": staged,
                     "consumption": {"baton.directory/1": {"layout": "flat"}}}],
        "outputs": [{"name": PROPOSAL_TARGET,
                     "type": "directory-result",
                     "path": PROPOSAL_TARGET, "required": True,
                     "constraints": {"max_bytes": MAX_SOURCE_BYTES,
                                     "max_entries": MAX_SOURCE_ENTRIES,
                                     "allowed_media_types":
                                         ["application/octet-stream",
                                          "text/plain"],
                                     "link_policy": "forbid",
                                     "validator_digest": None}}],
        "role_instructions_digest": role_instructions_digest,
        "runtime_profile_digest": runtime_profile_digest,
        "toolchain_digest": toolchain_digest,
        "worker_image_digest": worker_image_digest,
        **dict(policies)})


def assignment_manifest(*, given, work_ref, participant, generation,
                        attempt_id, offer_id, claim_receipt_digest,
                        claim_event_seq, created_at, activated_at,
                        assignment_contract, manifest_id):
    """The assignment minted for THIS attempt against THAT input manifest."""
    return _sealed({
        "version": {"major": 1, "minor": 0},
        "manifest_id": manifest_id,
        "created_at": created_at,
        "extensions": {},
        "schema": "baton.worker-manifest/assignment",
        "assignment_ref": {"work_ref": dict(work_ref),
                           "participant": participant,
                           "generation": generation},
        "assignment_contract": assignment_contract,
        "offer_id": offer_id,
        "runtime_attempt_id": attempt_id,
        "input_manifest_digest": given["manifest_digest"],
        "policy_digest": given["policy_digest"],
        "runtime_profile_digest": given["runtime_profile_digest"],
        "claim_receipt_digest": claim_receipt_digest,
        "claim_event_seq": claim_event_seq,
        "activated_at": activated_at})


def _sealed(document):
    """The document's own digest, over the document without it.

    Through the contracts package's canonical digest rather than a local
    hash: the manager recomputes it with that one, and two spellings of one
    digest is two documents.
    """
    from baton_v12.contracts import digest

    document.pop("manifest_digest", None)
    document["manifest_digest"] = digest(document)
    return document


# THE ONE DECLARED OUTPUT'S NAME, and the three files an operator reads out of
# it. `result.json` and `change.patch` are the WORKER's account and are never
# what this operator trusts -- the parent finding says so in terms, and
# `_derived` below is why: the diff and the verification are recomputed here
# from the collected bytes.
PROPOSAL_MEMBERS = ("candidate", "change.patch", "result.json",
                    "verification.txt")

# THE WORKER'S OWN PROGRAM, and the bound one conversation is given. Both are
# this deployment's constants rather than operands: the program is W6633's
# file at the image's own path, and a conversation a caller could lengthen is
# a bound a caller could remove.
# THE DOGFOOD IMAGE'S OWN ENTRY, and not the worker module underneath it.
#
# DEFECT, found while composing the real-engine gate: this named
# `baton_worker.py`, which `exec`s the worker with `agent=None` -- and
# `main` then falls back to `_scripted_default()`, the M2 FIXTURE agent.
# Against this image that is wrong twice over. It is wrong in principle,
# because a supervised pilot would have reported a result produced by a stub
# as the worker's work; and it is wrong in fact, because W39770 removed
# `scripted_agent.py` from this image, so the fallback dies
# `ModuleNotFoundError` and the conversation is lost for a reason that names
# nothing true about the attempt.
#
# `dogfood_entry.py` is the documented injection seam -- one line, in a file,
# calling `baton_worker.main(agent=ClaudeAgent())` -- and it is what the
# image's own ENTRYPOINT names. The transport `exec`s a second copy of it
# because PID 1 is idle by design; the program is the same program.
WORKER_PROGRAM = ["python3", "/opt/baton/dogfood_entry.py"]
CONVERSATION_SECONDS = 3900

# WHAT THE CONVERSATION ASKS FOR, in order. `describe` first because a worker
# that cannot describe itself is one this operator should not hand an
# assignment to, and the ordering is the transport's own: one exec session,
# two correlated operations, each consumed once.
CONVERSATION = ("describe", "work")


# EXACTLY WHAT AN EVIDENCE DOCUMENT IS. Held as a closed set rather than
# "whatever the arc put in the dict", because this is the one document that
# leaves this process and lands on an operator's disk: a member added upstream
# without thought would otherwise ride out to a durable file unexamined, which
# is precisely how raw provider text got into `result.json` in W39357.
EVIDENCE_MEMBERS = (
    "schema", "attempt_id", "task_id", "input_manifest_digest",
    "assignment_manifest_digest", "source_tree_digest", "worker_image_digest",
    "network", "runtime_id", "offer_id", "conversation", "worker_disposition",
    "output", "cleanup", "independent", "resolved", "unresolved",
    # Review 2026-08-30T14:59:53Z [P0] and [P1]: the retry could skip a REFUSED
    # `decide_retention` and pass anyway, because nothing recorded whether
    # retention had committed; and the route and policy it hands on were taken
    # from the grants without ever being bound to the attempt the record is
    # about.
    "retention", "review_route", "retention_policy_digest",
    # W39358 review 2026-08-30T14:46:24Z [P0]: the record carried no exact
    # assignment, so a closed valid one could be paired with ANOTHER
    # assignment's grants -- the pass would take its generation from the
    # grants and its operation id, runtime and settlement attempt from the
    # evidence. Member presence is not provenance.
    "work_ref", "participant", "generation",
    # ...and the members the post-start owner adds as it goes.
    "quiescence", "intake_receipt", "custody", "review_pass", "abandoned",
    "observed_after")

# A CEILING ON WHAT IS WRITTEN, not a truncation of what happened. Prose in
# this document is manager refusal text and this deployment's own sentences;
# an unbounded one would be an unbounded durable write driven by an untrusted
# failure path.
MAX_EVIDENCE_BYTES = 256 * 1024


def write_evidence(evidence, place):
    """The retained record, written ONCE and proved clean before it is.

    THREE HOLDS, IN THIS ORDER, and the order is the point.

    First the §13 sweep, over the WHOLE document at any depth, using the
    manager's own owner rather than a second spelling of it. A bearer that
    reached a refusal message would be as durable here as one written to a
    member of its own, and this file is the most durable surface this
    deployment has.

    Then the closed member set. What this arc composes is identities,
    dispositions and this operator's INDEPENDENT derivation -- never the
    worker's account and never a captured stream -- and an unexpected member
    is refused rather than written, because the reason it is unexpected is
    that nobody decided it was safe to keep.

    Then the ceiling, before the write rather than after it.

    THE WRITE IS ATOMIC AND DURABLE. Composed beside the destination and
    renamed onto it, so a reader never sees a partial evidence document and a
    crash mid-write leaves the previous one intact; the directory is synced
    because the rename is the act that has to survive.
    """
    import tempfile

    from baton_v12.contracts import check_no_durable_secret

    if type(evidence) is not dict:
        raise OperatorRefusal(
            f"the evidence written for an operator is one document; this is a "
            f"{type(evidence).__name__}")
    try:
        check_no_durable_secret(evidence, "a dogfood evidence record")
    except ContractRefusal as refused:
        # THE OPERATOR'S OWN VOCABULARY at the operator's own boundary, and
        # the manager's sentence kept inside it rather than replaced.
        raise OperatorRefusal(
            f"this evidence record will not be written: {refused.message}")
    missing = sorted(one for one in EVIDENCE_MEMBERS if one not in evidence)
    extra = sorted(one for one in evidence if one not in EVIDENCE_MEMBERS)
    if missing or extra:
        raise OperatorRefusal(
            "an evidence record is exactly the members this operator composes"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    body = json.dumps({one: evidence[one] for one in EVIDENCE_MEMBERS},
                      indent=2, sort_keys=True).encode("utf-8")
    if len(body) > MAX_EVIDENCE_BYTES:
        raise OperatorRefusal(
            f"this evidence record is {len(body)} bytes and this operator "
            f"writes at most {MAX_EVIDENCE_BYTES}; an unbounded durable write "
            f"driven by a failure path is not evidence")
    directory = os.path.dirname(os.path.abspath(place)) or "."
    handle, staged = tempfile.mkstemp(prefix=".evidence-", dir=directory)
    try:
        with os.fdopen(handle, "wb") as writing:
            writing.write(body)
            writing.flush()
            os.fsync(writing.fileno())
        os.replace(staged, place)
    except BaseException:
        if os.path.exists(staged):
            os.unlink(staged)
        raise
    opened = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(opened)
    finally:
        os.close(opened)
    return place


def run_dogfood_task(*, engine, run, open_channel, store, port, session,
                     adapter_of, review_route,
                     attempt_id, offer_id, source, task_path, storage,
                     launch_home, credential_delivery, image_digest, network,
                     work_ref, participant, generation, now, policies,
                     record_binding, assignment_contract, human_contract,
                     role_instructions_digest, runtime_profile_digest,
                     toolchain_digest, adapter_digest, adapter_name,
                     labels, retention_policy_digest,
                     retention_disposition, bearer,
                     seconds=CONVERSATION_SECONDS):
    """ONE supervised dogfood attempt, composed from public operations only.

    THE ORDER IS THE ACCEPTED ARC and this function's whole job is to be the
    one place it is written down: authority half, delivery half, the two
    manager roots, one container and one conversation, output custody, and
    the ending. Every step is a `baton_v12.worker_manager` operation; nothing
    here journals, reads a control-store table, or invents a state.

    IT ANSWERS EVIDENCE AND RAISES NOTHING IT CAN ACCOUNT FOR. What comes back
    is the retained record an operator reads -- identities, dispositions and
    the INDEPENDENTLY derived diff and verification result -- and `resolved`
    is false whenever a proof this arc requires was not obtained.
    """
    from baton_v12.worker_manager import (accept_offer, activate_assignment,
                                          authorize_cleanup, decide_retention,
                                          issue_offer, observe, record_attempt,
                                          reconcile_runtime, request_freeze,
                                          request_intake,
                                          request_runtime_start,
                                          retain_manifest, submit_claim)
    from baton_v12.worker_manager import launch, worker_entry, workspaces

    task = frozen_task(task_path)
    preflight(task=task, policies=policies,
              worker_image_digest=image_digest,
              toolchain_digest=toolchain_digest,
              runtime_profile_digest=runtime_profile_digest,
              role_instructions_digest=role_instructions_digest,
              record_binding=record_binding, network=network,
              review_route=review_route,
              retention_disposition=retention_disposition,
              human_contract=human_contract)
    # THE SESSION IS TAKEN AS AN OPERAND AND NOT READ OFF THE PORT. It is the
    # SAME facade the caller constructed `port` with -- but reaching into
    # `port._session` for it would be helping myself to a private attribute of
    # another module to obtain a capability, which is the exact mistake review
    # 2026-08-30T06:44:13Z caught in `_derived` reaching for `adapter._custody`.
    # A capability this deployment uses is a capability it was given.
    if not callable(getattr(session, "pass_work", None)):
        raise OperatorRefusal(
            "this deployment passes the assignment to its review route when "
            "the attempt succeeds, and the session it was given has no "
            "callable pass_work")

    # -- the delivery half, before the authority half touches anything ------
    #
    # STAGED FIRST BECAUSE THE OFFER FREEZES ITS DIGEST. `issue_offer` binds
    # the input manifest digest, and the manifest describes the staged tree --
    # so the tree has to exist before there is a digest to freeze.
    group = _configured_group(store)
    roots = workspaces.assignment_workspace(group, storage, attempt_id)
    staged = stage_source(source, roots["inputs"])
    given = input_manifest(
        work_ref=work_ref, staged=staged, created_at=now,
        manifest_id=f"input-{attempt_id}",
        assignment_contract=assignment_contract, human_contract=human_contract,
        record_binding=record_binding,
        role_instructions_digest=role_instructions_digest,
        runtime_profile_digest=runtime_profile_digest,
        toolchain_digest=toolchain_digest, worker_image_digest=image_digest,
        policies=policies)

    # -- the authority half -------------------------------------------------
    issue_offer(store, port, offer_id=offer_id,
                work_id=work_ref["work_id"], runtime_attempt_id=attempt_id,
                input_digest=given["manifest_digest"],
                policy_digest=given["policy_digest"],
                profile_digest=runtime_profile_digest,
                profile_name="dogfood", mint_bearer=lambda: bearer)
    accepted = accept_offer(store, port, offer_id=offer_id, decision="accept",
                            bearer=bearer, now=now,
                            runtime_attempt_id=attempt_id,
                            work_ref=dict(work_ref))
    record_attempt(store, attempt_id=attempt_id, adapter_name=adapter_name,
                   adapter_digest=adapter_digest,
                   profile_digest=runtime_profile_digest,
                   input_digest=given["manifest_digest"],
                   policy_digest=given["policy_digest"])
    # THE CLAIM'S OWN ANSWER IS KEPT. Review 2026-08-30T06:35:56Z [P0]: this
    # discarded it and populated the assignment manifest from the
    # `offer.accepted` document, which carries neither a claim event nor a
    # receipt digest -- so `_claim_receipt` wrote an all-zero digest and
    # `_claim_event` wrote 1. A syntactically valid placeholder in an
    # assignment manifest is INVENTED AUTHORITY EVIDENCE, which is worse than
    # an absent field because it reads as a fact.
    claimed = submit_claim(store, port, offer_id=offer_id)
    expect = {"work_ref": dict(work_ref), "participant": participant,
              "generation": generation}
    activate_assignment(store, port, attempt_id=attempt_id,
                        expect=dict(expect))

    assignment = assignment_manifest(
        given=given, work_ref=work_ref, participant=participant,
        generation=generation, attempt_id=attempt_id, offer_id=offer_id,
        claim_receipt_digest=_claim_receipt(claimed),
        claim_event_seq=_claim_event(claimed), created_at=now,
        activated_at=now, assignment_contract=assignment_contract,
        manifest_id=f"assignment-{attempt_id}")
    # THE TASK IS WRITTEN BEFORE THE ROOT IS SEALED, and the order is not a
    # preference. `compose_input_root` exposes the whole surface READ-ONLY as
    # its last act -- `r-xr-xr-x` on the input root -- so a write afterwards
    # is a `PermissionError` and this arc could not run at all.
    #
    # HOW IT SURVIVED NINE ROUNDS: every composition case so far patched
    # `compose_input_root` to a no-op, so the seal never happened and the copy
    # always succeeded. The replay matrix this round is the first case to run
    # the real one, and it failed on the first attempt. A mock that removes
    # the very act an ordering depends on cannot observe the ordering.
    #
    # It stays out of the input MANIFEST either way -- that is pinned, and
    # unaffected: the manifest was composed from the staged tree above and
    # names nothing here.
    _copied_task(task, roots["inputs"])
    workspaces.compose_input_root(
        roots["inputs"], given, assignment,
        assignment=dict(assignment["assignment_ref"]),
        runtime_attempt_id=attempt_id)
    # THE MANAGER HOLDS THE MANIFEST IT WILL COMPARE AGAINST. A freeze refuses
    # an attempt whose input manifest this manager never retained.
    retain_manifest(store, given, "inputManifest")

    # -- the two manager roots, and the one container -----------------------
    delivery = launch.materialize(launch_home,
                                  **_launch_operands(attempt_id, task))
    declared = [dict(one) for one in given["outputs"]]
    # THE FACTORY IS GIVEN THE SAME GRANTS THIS RUN RECORDS. Review
    # 2026-08-30T06:35:56Z [P1]: it received neither the engine, the resolved
    # image digest, the network nor the labels -- so the evidence could name
    # one image and network while an unchecked closure built an adapter for
    # another. `run` and `labels` were accepted and unused for the same reason
    # and are passed through here rather than dropped, because an adapter that
    # cannot select this attempt's runtimes cannot reconcile them.
    adapter = adapter_of(engine=engine, run=run, image_digest=image_digest,
                         network=network, labels=dict(labels), roots=roots,
                         declared=declared, launch=delivery,
                         credential_delivery=credential_delivery,
                         input_manifest_digest=given["manifest_digest"])
    # THE RUNTIME IDENTITY COMES BACK FROM THE OPERATION, not from a row.
    # `request_runtime_start` journals the start and answers through
    # `reconcile_runtime`, whose `runtime.attached` document carries
    # `runtime_id` -- so the transport's operand is the manager's own answer
    # rather than something this deployment read out of a table it must not
    # open. An UNCERTAIN reconciliation carries no identity, and that is a
    # fact about the attempt rather than a value to go looking for.
    started = request_runtime_start(store, adapter, attempt_id=attempt_id,
                                    inputs=roots["inputs"])
    runtime_id = started.get("runtime_id") if type(started) is dict else None

    if runtime_id is None:
        decided = started.get("decision") if type(started) is dict else None
        raise OperatorRefusal(
            f"the start of attempt {attempt_id} reconciled to "
            f"{decided!r} without naming a runtime; a conversation needs the "
            f"exact runtime, and this deployment does not go looking for one "
            f"the manager did not name")

    # EVERY MEMBER EXISTS FROM THE START, and that is what makes an ABSENT
    # one mean something. `write_evidence` holds this document to a closed
    # set, so a record composed member-by-member as the arc happened to reach
    # them would have a different shape per outcome and no shape to hold. A
    # step that did not run leaves its member `None`, which is a fact an
    # operator can read; a member that is not there at all is a question.
    evidence = {"schema": "baton.dogfood-evidence/1",
                "attempt_id": attempt_id, "task_id": task["task_id"],
                "input_manifest_digest": given["manifest_digest"],
                "assignment_manifest_digest": assignment["manifest_digest"],
                "source_tree_digest": staged["tree_digest"],
                "worker_image_digest": image_digest, "network": network,
                "work_ref": dict(work_ref), "participant": participant,
                "generation": generation,
                "runtime_id": runtime_id, "offer_id": offer_id,
                "conversation": None, "worker_disposition": None,
                "output": None, "cleanup": None, "quiescence": None,
                "intake_receipt": False, "custody": None, "review_pass": None,
                "abandoned": None, "observed_after": None,
                "review_route": review_route, "retention": None,
                "retention_policy_digest": retention_policy_digest,
                "independent": None, "resolved": False, "unresolved": []}

    # -- EVERYTHING AFTER THE START IS THE ENDING'S -------------------------
    #
    # Review 2026-08-30T06:44:13Z [P0]: the conversation used to happen HERE,
    # and its two failure branches returned before the guard -- so a container
    # this deployment had started was left running whenever the worker did not
    # answer, which is precisely the case the guard exists for. Successful
    # conversation is not a precondition for entering an ending; a STARTED
    # RUNTIME is.
    return _after_start(store, port, session, adapter, evidence,
                        engine=engine, open_channel=open_channel,
                        attempt_id=attempt_id, runtime_id=runtime_id,
                        roots=roots, task=task,
                        source=os.path.join(roots["inputs"], SOURCE_TARGET),
                        expect=dict(expect), review_route=review_route,
                        retention_policy_digest=retention_policy_digest,
                        retention_disposition=retention_disposition,
                        seconds=seconds)


class _Lost(Exception):
    """One named reason this attempt cannot reach a supervised result.

    Raised rather than returned, so every one of them lands in the same
    ending. The sixth and seventh rounds both claimed a common ending while
    returning around it from three places; an exception is the shape that
    cannot be forgotten at a call site.
    """


def _after_start(store, port, session, adapter, evidence, *, engine,
                 open_channel, attempt_id, runtime_id, roots, task, source,
                 expect, review_route, retention_policy_digest,
                 retention_disposition, seconds):
    """ONE owner for every branch after a runtime exists.

    Review 2026-08-30T06:44:13Z [P0], twice over. The conversation was outside
    the guard and the guard's own early returns skipped the ending, so the
    record's "the manager's own cleanup is attempted, whatever happened" was
    stronger than the code for the third round running. Everything is inside
    now, every named reason is raised rather than returned, and the ending
    runs in `finally`.

    AN UNEXPECTED FAULT IS RECORDED AND THEN PROPAGATES. Review [P1]: catching
    every `Exception` turned a `KeyError` in this module into a supervised
    attempt outcome. Cleanup still runs -- that is what `finally` is for -- but
    an implementation defect is not an ending an operator should read as one.
    """
    from baton_v12.worker_manager import worker_entry

    try:
        spoken = worker_entry.converse(
            worker_entry.ChannelPort(open_channel), engine=engine,
            runtime_id=runtime_id, program=WORKER_PROGRAM,
            session=f"session-{attempt_id}", operations=list(CONVERSATION),
            seconds=seconds,
            operation_ids=[f"{one}:{attempt_id}" for one in CONVERSATION])
        evidence["conversation"] = {
            "ending": spoken["ending"], "why": spoken["why"],
            "answered": [one.get("operation") for one in spoken["answers"]]}
        if spoken["ending"] != "answered":
            # THE TRANSPORT'S OWN VOCABULARY, reported rather than translated
            # into a disposition nobody observed.
            raise _Lost(f"the worker-entry conversation ended "
                        f"{spoken['ending']}")
        disposition = _disposition_of(spoken)
        if disposition is None:
            raise _Lost("the worker answered no disposition")
        evidence["worker_disposition"] = disposition
        _custody(store, port, session, adapter, evidence,
                 attempt_id=attempt_id, runtime_id=runtime_id, task=task,
                 source=source, disposition=disposition,
                 expect=expect, review_route=review_route,
                 retention_policy_digest=retention_policy_digest,
                 retention_disposition=retention_disposition)
    except _Lost as why:
        _unresolved(evidence, str(why))
    except ContractRefusal as refused:
        _unresolved(evidence, f"a manager contract declined: "
                              f"{refused.message}")
    except BaseException as failed:                        # noqa: BLE001
        _unresolved(evidence, f"the attempt ended on an unexpected "
                              f"{type(failed).__name__}")
        # THE EVIDENCE RIDES OUT WITH THE FAULT. Approver ruling item 8: a
        # post-start unexpected fault must still leave durable unresolved
        # evidence. The record is local to `run_dogfood_task`, so a launcher
        # catching the propagating fault has no other way to reach it -- and a
        # container that started and an attempt that is now unresolved is
        # exactly the case an operator most needs the file for.
        failed.dogfood_evidence = evidence
        raise
    finally:
        _ended_however(store, port, adapter, evidence, attempt_id=attempt_id,
                       runtime_id=runtime_id,
                       retention_policy_digest=retention_policy_digest)
    return evidence


def _custody(store, port, session, adapter, evidence, *, attempt_id,
             runtime_id, task, source, disposition, expect, review_route,
             retention_policy_digest, retention_disposition):
    """Quiescence, freeze, intake, the derivation, retention, and the pass.

    EVERY REASON IT CANNOT PROCEED IS RAISED. `_after_start` owns the ending,
    so nothing here returns early -- the third round in a row that mistake was
    made is the reason this function has no `return` on a failure path at all.
    """
    from baton_v12.worker_manager import (decide_retention, observe,
                                          reconcile_runtime, request_freeze,
                                          request_intake)

    # QUIESCENCE IS ORDERED, NOT WAITED FOR. The accepted transport starts the
    # container INTERACTIVE so idle PID 1 outlives the exec'd worker program,
    # and `reconcile_runtime` observes rather than stops.
    stopped = adapter.stop({"runtime_id": runtime_id,
                            "operation_id": f"quiesce:{attempt_id}"})
    evidence["quiescence"] = {"ordered": stopped.get("ordered"),
                              "state": stopped.get("state"),
                              "why": stopped.get("why")}
    # ONLY `quiescent`, AND `absent` IS NOT THE SAME PROOF. Review
    # 2026-08-30T06:44:13Z [P1]: this accepted both and went on to freeze. The
    # freeze contract takes `quiescent` alone and says why -- a runtime that
    # is merely GONE was never observed to have finished writing, so freezing
    # its output would seal bytes nobody watched the end of.
    if stopped.get("state") != "quiescent":
        raise _Lost(f"the runtime was ordered to stop and observed "
                    f"{stopped.get('state')!r}; a freeze takes a positively "
                    f"quiescent runtime, and an absent one is not the same "
                    f"proof because its writer was never seen to finish")
    reconcile_runtime(store, adapter, attempt_id=attempt_id)
    observe(store, attempt_id=attempt_id, axis="worker_disposition",
            value=disposition)
    # THE FROZEN OUTPUT IS RECORDED. A verified custody receipt is not yet the
    # retained handoff result: the freeze is what makes the bytes the ones the
    # pass hands on, and a retry that could not see it would resume an
    # ordering that never completed.
    frozen = request_freeze(store, port, adapter, attempt_id=attempt_id,
                            disposition=disposition)
    # THE EXACT ANSWER, WITH NO DEFAULT INVENTED FOR IT. Review
    # 2026-08-30T15:10:12Z [P0]: this wrote `frozen=True` unconditionally and
    # filled the retention disposition in from the REQUEST when the manager's
    # answer omitted it -- so the record asserted facts the manager had not
    # necessarily committed, and a retry then read that assertion back as
    # proof. What is recorded here is what the manager said.
    evidence["output"] = {"manifest_digest": frozen["manifest_digest"],
                          "result_id": frozen["result_id"]}
    receipt = request_intake(store, port, adapter, attempt_id=attempt_id)
    # THE RECEIPT IS THE AUTHORIZATION, AND ITS CONTENTS ARE NOT. Recorded the
    # moment intake commits, before anything is asked about what it holds:
    # `authorize_cleanup` is authorized by the receipt existing, so an EMPTY
    # one still ends the attempt through the ordinary path. My first cut set
    # this after the emptiness check, which sent an attempt that had a
    # perfectly good receipt down the abandonment ending instead -- declaring
    # a human decision over an attempt the manager could already end.
    # THE RECEIPT'S OWN DIGEST, not a boolean. Review 2026-08-30T15:25:10Z
    # [P0]: `True` is a claim with nothing to compare, so the retry could
    # check that intake had happened and not that THIS receipt was the one.
    evidence["intake_receipt"] = {
        "receipt_digest": receipt["receipt_digest"]}
    held = list(receipt["artifacts"])
    if not held:
        raise _Lost("intake took custody of nothing, so there is no proposal "
                    "to account for")
    # THE PUBLIC LOCATOR, from the receipt. `intake_artifact` carries
    # `custody_locator` precisely so a caller does not reach into the adapter.
    # ...AND ITS PUBLIC LOCATOR, which W51473 makes part of the record rather
    # than a value only `_derived` ever looked at. A retained candidate whose
    # locator an operator cannot read out of the evidence is a candidate the
    # independent diff cannot be performed on -- which is precisely what the
    # first live attempt discovered, from the other end.
    evidence["custody"] = sorted(
        ({"artifact_id": one["artifact_id"],
          "content_digest": one["content_digest"],
          "bytes": one["bytes"],
          "custody_locator": one["custody_locator"]} for one in held),
        key=lambda one: one["artifact_id"])
    # DERIVED BEFORE RETENTION DISCARDS THE BYTES, which is the ordering the
    # parent finding requires.
    evidence["independent"] = _derived(held[0]["custody_locator"], task,
                                       source)
    # RECORDING A CHECK IS NOT PASSING IT. Review 2026-08-30T14:36:46Z [P0]:
    # `_derived` wrote `verification_status` and this went straight on to
    # retention and the pass, so a candidate whose frozen task verification
    # exited nonzero received the SAME successful authority pass as a verified
    # one. The acceptance's whole point is an INDEPENDENTLY derived
    # verification, and approver ruling M46985 authorizes handing on a
    # VERIFIED result -- a failed check is neither.
    #
    # RAISED, so the receipt-authorized ending still runs: intake committed,
    # so the manager is still asked to settle. What does not happen is the
    # pass, which is the one thing a failed verification must not earn.
    if evidence["independent"]["verification_status"] != 0:
        raise _Lost(
            f"the task's own verification exited "
            f"{evidence['independent']['verification_status']} over the "
            f"candidate this operator rederived; a recorded check is not a "
            f"passed one, and an unverified candidate is not handed to review")
    # THE COMMITTED DECISION IS RECORDED, not merely performed. A retry that
    # could not tell a committed retention from a refused one would hand a
    # result to review whose untrusted material nobody had decided about.
    decided = decide_retention(
        store, port, adapter, attempt_id=attempt_id,
        artifact_ids=[one["artifact_id"] for one in held],
        disposition=retention_disposition,
        retention_policy_digest=retention_policy_digest)
    # TAKEN FROM THE DECISION ITSELF rather than recomposed from the request:
    # a member the writer composes out of what it ASKED for is not a record of
    # what the manager DECIDED.
    evidence["retention"] = {
        "disposition": decided["disposition"],
        "retention_policy_digest": decided["retention_policy_digest"],
        "artifact_ids": sorted(one["artifact_id"] for one in held)}
    # AND THEN THE WORK GOES TO REVIEW, which is where the v11 lifecycle this
    # deployment is dogfooding actually ends. Approver ruling M44657: after
    # successful intake, independent verification and retention, pass the
    # EXACT assignment generation to the operator-supplied review Route.
    #
    # ORDERED HERE, LAST, AND THAT ORDER IS THE RULING'S. The pass both moves
    # the Route and ENDS the assignment in one authority act, so cleanup --
    # which runs in `_ended_however` after this returns -- necessarily happens
    # on an assignment that is over. Cleaning up first would tear down the
    # runtime of an assignment the authority still considered live, which is
    # the same boundary W44716 exists to keep straight.
    #
    # EFFECTIVELY ONCE BY IDENTITY. The operation id is derived from this
    # attempt, so an exact replay of the arc replays the authority's own
    # committed answer instead of passing a second time; a DIFFERENT
    # generation carries a different signature and collides rather than
    # silently reusing this one's pass.
    evidence["review_pass"] = _passed(session, expect, review_route,
                                      attempt_id=attempt_id)


def _passed(session, expect, review_route, *, attempt_id):
    """The authority's own answer to this deployment's pass, held to shape.

    WHAT IS KEPT IS WHAT THE AUTHORITY SAID, not what this deployment asked
    for. The route in the evidence is the route the authority recorded, so an
    operator reading the record afterwards is reading the transition that
    happened rather than the operand that requested it.
    """
    # ONE EXACT OPERAND DOCUMENT, which is the authority's own rule for every
    # session act -- "exactly one exact built-in operand document, taken
    # ONCE". W39358's real-authority gate is what found this: every case until
    # now used a fake that accepted keywords, so the deployment had been
    # calling a shape no real `Session` has.
    answered = session.pass_work({"expect": dict(expect),
                                  "operation_id": f"pass:{attempt_id}",
                                  "to_route": review_route,
                                  "comment": PASS_COMMENT})
    if type(answered) is not dict:
        raise _Lost(f"the authority answered the review pass with "
                    f"{type(answered).__name__} and this deployment reads a "
                    f"document")
    missing = sorted(one for one in PASS_MEMBERS if one not in answered)
    if missing:
        raise _Lost(f"the review pass answered without {', '.join(missing)}; "
                    f"a pass answers the ended assignment beside the route it "
                    f"moved the Work to, and a document missing either is not "
                    f"evidence this assignment ended")
    # THE ROUTE ECHO IS NOT THE PROOF, and taking it as one was the defect.
    # Review 2026-08-30T12:27:41Z [P0]: this accepted any document whose
    # `route` matched the operand, so an answer ABOUT ANOTHER GENERATION that
    # happened to echo `rview` was retained as this attempt's successful
    # review pass -- and cleanup then ran on the strength of a transition that
    # ended somebody else's assignment.
    #
    # THE RULING IS EXACT-ASSIGNMENT SHAPED, so the assignment the authority
    # says it ENDED is what is compared, and the route is checked beside it
    # rather than instead of it.
    if answered["assignment"] != expect:
        raise _Lost(f"the review pass ended {answered['assignment']!r} and "
                    f"this attempt holds {expect!r}; an answer about another "
                    f"assignment is not evidence that this one ended")
    if answered["route"] != review_route:
        raise _Lost(f"the assignment was passed to {answered['route']!r} and "
                    f"this deployment asked for {review_route!r}")
    # AND IT IS A PASS RATHER THAN SOME OTHER ENDING. `cause` is what tells
    # a release, a cancel and a pass apart in the authority's own vocabulary,
    # and a fenced ending is not the lifecycle transition this arc performs.
    if answered["cause"] != "pass" or answered["fenced"]:
        raise _Lost(f"the assignment ended {answered['cause']!r} with fenced "
                    f"{answered['fenced']!r}; the approved transition is an "
                    f"unfenced pass and nothing else is one")
    # AND THE WORK IS WHERE A PASS LEAVES IT. Review 2026-08-30T12:40:47Z
    # [P1]: requiring these two by NAME and then adopting whatever they said
    # meant an answer with `phase="active"` and a live quiescence gate was
    # recorded as the approved queued, ungated handoff. A member held only for
    # presence is a member not held.
    if answered["phase"] != "queued" or answered["gate"] is not None:
        raise _Lost(f"the assignment was passed into phase "
                    f"{answered['phase']!r} behind gate {answered['gate']!r}; "
                    f"the approved handoff leaves the Work queued and ungated "
                    f"for its review route to claim")
    return {"route": answered["route"], "cause": answered["cause"],
            "phase": answered["phase"], "gate": answered["gate"],
            "fenced": answered["fenced"],
            "assignment": dict(answered["assignment"])}


# THE CLOSED RESULT A PASS ANSWERS WITH. `AuthorityCore.pass_work` returns the
# ended assignment beside the new Route, and every member of it is read here --
# holding a document to the members it must carry is what makes the comparison
# below a comparison rather than a `get` that shrugs at an absence.
PASS_MEMBERS = ("assignment", "route", "cause", "phase", "gate", "fenced")

# WHAT A COMPLETED, TRUSTED RESULT LOOKS LIKE IN THIS DEPLOYMENT'S OWN RECORD.
# Approver ruling item 7 turns on this distinction: a successful worker whose
# result is frozen and independently verified is a DIFFERENT state from failed
# post-worker machinery, and only the second one is retried.
_TRUSTED_RESULT = ("worker_disposition", "intake_receipt", "custody",
                   "independent", "retention", "output")

# THE ONE DISPOSITION A HANDOFF PRESERVES. `schema.DISPOSITIONS` is
# `completed, unable, plan-rejected, cancelled` -- four terminal answers, and
# only the first is a result to hand to review. Review 2026-08-30T14:36:46Z
# [P0]: the hold was truthiness, so any non-empty string passed, and the
# positive case supplied the fixture word `succeeded` which is not in the
# worker's vocabulary at all -- so it proved nothing about the real state.
TRUSTED_DISPOSITION = "completed"

# WHAT EACH CONSUMED MEMBER OF A RETAINED RECORD IS. Review
# 2026-08-30T15:34:00Z [P1]: `read_evidence` proved the top-level member SET
# and the secret boundary, and neither of those makes an allowed member a
# DOCUMENT. A retained `True` where a projection belongs is untrusted operator
# input, and leaking `AttributeError` or `TypeError` out of it makes the
# documented retry an unsafe parser rather than a typed boundary.
_RETRY_SHAPE = {
    "output": {"manifest_digest": str, "result_id": str},
    "intake_receipt": {"receipt_digest": str},
    "retention": {"disposition": str, "retention_policy_digest": str,
                  "artifact_ids": list},
    "independent": {"verification_status": int},
}
_CUSTODY_SHAPE = {"artifact_id": str, "content_digest": str,
                  "bytes": int, "custody_locator": str}

# A CEILING ON THE HISTORY a retry reads back, for the same reason the record
# has one on the way out: an unbounded list in an editable file is an
# unbounded read driven by whoever edited it.
MAX_UNRESOLVED_REASONS = 256


def _held_record(evidence):
    """The nested contract, proved BEFORE any member is consumed.

    ONE PASS OVER EVERY MEMBER THE RETRY READS, and it runs first: a document
    checked as it is used is a document that has already been used wrongly by
    the time the check fails. What comes back is the same record; what does
    not come back is an exception type a caller cannot act on.
    """
    for member, contract in _RETRY_SHAPE.items():
        held = evidence.get(member)
        if type(held) is not dict:
            raise OperatorRefusal(
                f"the retained record's {member} is a "
                f"{type(held).__name__} and this operator reads a document "
                f"naming {', '.join(sorted(contract))}")
        for name, kind in contract.items():
            value = held.get(name)
            # `bool` IS an `int` in Python and is not one here: a retained
            # `True` verification status is a claim nobody measured.
            if type(value) is not kind:
                raise OperatorRefusal(
                    f"the retained record's {member}.{name} is a "
                    f"{type(value).__name__} and this operator reads a "
                    f"{kind.__name__}")
        if member == "retention":
            for one in held["artifact_ids"]:
                if type(one) is not str:
                    raise OperatorRefusal(
                        f"the retained record names a retained artifact that "
                        f"is a {type(one).__name__} and an artifact id is "
                        f"durable text")
    # THE RETRY-OWNED HISTORY, which this function consumes as much as the
    # projections do. Review [P1]: `historical = list(evidence["unresolved"])`
    # leaked a raw `TypeError` for an editable boolean, so a member used to
    # DECIDE and to REPORT was the one member not held.
    unresolved = evidence.get("unresolved")
    if type(unresolved) is not list:
        raise OperatorRefusal(
            f"the retained record's unresolved is a "
            f"{type(unresolved).__name__} and this operator reads a list of "
            f"reasons")
    if len(unresolved) > MAX_UNRESOLVED_REASONS:
        raise OperatorRefusal(
            f"the retained record carries {len(unresolved)} unresolved "
            f"reasons and this operator reads at most "
            f"{MAX_UNRESOLVED_REASONS}")
    for one in unresolved:
        if type(one) is not str:
            raise OperatorRefusal(
                f"the retained record names an unresolved reason that is a "
                f"{type(one).__name__} and a reason is durable text")
    for member in ("attempt_id", "runtime_id", "worker_disposition"):
        if type(evidence.get(member)) is not str:
            raise OperatorRefusal(
                f"the retained record's {member} is a "
                f"{type(evidence.get(member)).__name__} and this operator "
                f"reads durable text")
    if evidence.get("review_pass") is not None \
            and type(evidence["review_pass"]) is not dict:
        raise OperatorRefusal(
            f"the retained record's review_pass is a "
            f"{type(evidence['review_pass']).__name__} and this operator "
            f"reads a document or nothing")
    custody = evidence.get("custody")
    if type(custody) is not list or not custody:
        raise OperatorRefusal(
            f"the retained record's custody is a "
            f"{type(custody).__name__} and this operator reads a non-empty "
            f"list of artifacts")
    for one in custody:
        if type(one) is not dict:
            raise OperatorRefusal(
                f"the retained record names a custody artifact that is a "
                f"{type(one).__name__} and this operator reads a document")
        for name, kind in _CUSTODY_SHAPE.items():
            if type(one.get(name)) is not kind:
                raise OperatorRefusal(
                    f"a retained custody artifact's {name} is a "
                    f"{type(one.get(name)).__name__} and this operator reads "
                    f"a {kind.__name__}")
    return evidence


def _committed(store, evidence):
    """The manager's OWN answers, read back and held against the record.

    THREE PUBLIC READERS AND NO OTHER ROUTE. `frozen_output_of`,
    `intake_receipt_of` and `retentions_of` are what the manager will say
    about this attempt; a retry that believed the file instead would be
    letting a text editor authorize a handoff.

    ABSENCE, DISAGREEMENT OR AN INCOMPLETE DECISION ALL REFUSE, and they are
    the same answer for the same reason: the ending this retry is trying to
    finish was composed from acts that must have happened, and a record is
    evidence of them only where the journal agrees.
    """
    from baton_v12.worker_manager import (frozen_output_of, intake_receipt_of,
                                          retentions_of)

    attempt_id = evidence["attempt_id"]
    frozen = frozen_output_of(store, attempt_id)
    if frozen is None:
        raise OperatorRefusal(
            f"the manager has no frozen result for attempt {attempt_id!r}; a "
            f"handoff retry hands on a frozen result and this record names "
            f"one the manager did not commit")
    # EVERY RECORDED MEMBER IS HELD. Review 2026-08-30T15:25:10Z [P0], and the
    # rule it states is the one to keep: a member the writer claims and the
    # reader ignores is an editable alternate fact. So each projection below
    # is compared whole rather than by selected names.
    named = evidence["output"] or {}
    for member in ("manifest_digest", "result_id"):
        if frozen[member] != named.get(member):
            raise OperatorRefusal(
                f"the retained record names frozen {member} "
                f"{named.get(member)!r} and the manager committed "
                f"{frozen[member]!r}")
    receipt = intake_receipt_of(store, attempt_id)
    if receipt is None:
        raise OperatorRefusal(
            f"the manager has no intake receipt for attempt {attempt_id!r}; "
            f"the receipt is what authorizes the ending this retry finishes")
    recorded = evidence["intake_receipt"] or {}
    if receipt["receipt_digest"] != recorded.get("receipt_digest"):
        raise OperatorRefusal(
            f"the retained record names intake receipt "
            f"{recorded.get('receipt_digest')!r} and the manager committed "
            f"{receipt['receipt_digest']!r}")
    # THE WHOLE CUSTODY PROJECTION -- identity, content and size. Comparing
    # ids alone would let an edited content digest or byte count ride through
    # on a matching name.
    committed = sorted(
        ({"artifact_id": one["artifact_id"],
          "content_digest": one["content_digest"], "bytes": one["bytes"],
          "custody_locator": one["custody_locator"]}
         for one in receipt["artifacts"]),
        key=lambda one: one["artifact_id"])
    if committed != sorted(evidence["custody"],
                           key=lambda one: one["artifact_id"]):
        raise OperatorRefusal(
            f"the retained record and the manager's intake receipt describe "
            f"different custody for attempt {attempt_id!r}")
    held = [one["artifact_id"] for one in committed]
    decided = retentions_of(store, attempt_id)
    if not decided:
        raise OperatorRefusal(
            f"the manager holds no retention decision for attempt "
            f"{attempt_id!r}; the required ordering never completed")
    named = evidence["retention"]
    if sorted(named.get("artifact_ids") or ()) != held:
        raise OperatorRefusal(
            f"the retained record names retained artifacts "
            f"{named.get('artifact_ids')!r} and intake took custody of "
            f"{held!r}")
    if sorted(one["artifact_id"] for one in decided) != held:
        raise OperatorRefusal(
            f"the manager's retention decisions do not cover exactly the "
            f"artifacts intake took custody of for attempt {attempt_id!r}; an "
            f"incomplete decision is not a completed ordering")
    for one in decided:
        if one["disposition"] != named.get("disposition") \
                or one["retention_policy_digest"] != named.get(
                    "retention_policy_digest"):
            raise OperatorRefusal(
                f"the retained record names retention "
                f"{named.get('disposition')!r} under "
                f"{named.get('retention_policy_digest')!r} and the manager "
                f"committed {one['disposition']!r} under "
                f"{one['retention_policy_digest']!r}")
    return evidence


# THE SENTENCES A RETRY PERFORMS THE ACTS FOR, matched on their openings so a
# retry settles what it redid and nothing else. All three are this
# deployment's own wording for the pass and the settlement.
_RETRY_OWNS = ("the manager declined to end the attempt:",
               "the manager declined to abandon the attempt:",
               "cleanup ended",
               "a manager contract declined:")


def retry_handoff(store, port, session, adapter, evidence, *, expect,
                  review_route, retention_policy_digest):
    """Retry ONLY the handoff, over a result that is already trusted.

    Approver ruling item 7. A worker that succeeded, whose output was frozen
    and whose candidate this operator independently rederived and verified, is
    not made untrustworthy by a `pass_work` that refused afterwards or a
    settlement that could not finish. Abandoning it would throw away a
    completed piece of work over a failure in the machinery AFTER it; opening
    another provider turn would pay for that work twice and produce a second,
    different result.

    SO THIS DOES EXACTLY TWO THINGS: the pass, and the ending. And it is
    defined as much by what it does NOT do, each of which is a thing a
    "just run it again" retry would have done:

      no restage        -- the input root is sealed and already measured;
      no reassignment   -- the SAME generation, or the pass is not this pass;
      no runtime start  -- nothing is launched, and nothing is stopped either,
                           because the arc already quiesced it cleanly;
      no provider turn  -- no claim, no offer, no bearer;
      no worker run     -- no conversation, no `exec`, no container;
      no freeze         -- the output is frozen and freezing is once;
      no rederivation   -- the diff and the verification stand as recorded.

    IDEMPOTENT AT BOTH STEPS. The pass carries the attempt's own operation
    identity, so the authority replays a committed one rather than passing
    twice; the ending is the manager's own operation, which replays likewise.
    Calling this on an attempt whose pass already committed does the ending
    and nothing else.

    IT REFUSES A RESULT THAT IS NOT TRUSTED, which is the whole of its
    licence. An attempt with no receipt, no custody or no independent
    derivation did not reach a result worth preserving, and its ending is
    W44716's abandonment rather than this.
    """
    # THE SHAPE BEFORE ANYTHING ELSE, because every check below reads members
    # of members and a `True` where a document belongs would fault rather than
    # refuse.
    _held_record(evidence)
    absent = [one for one in _TRUSTED_RESULT if not evidence.get(one)]
    if absent:
        raise OperatorRefusal(
            f"this attempt has no completed, independently verified result to "
            f"hand on ({', '.join(absent)} missing); a handoff retry preserves "
            f"a result that exists and does not manufacture one")
    # PRESENT IS NOT TRUSTED, and the two holds below are the difference.
    if evidence["worker_disposition"] != TRUSTED_DISPOSITION:
        raise OperatorRefusal(
            f"this attempt's worker answered "
            f"{evidence['worker_disposition']!r}; a handoff retry preserves a "
            f"{TRUSTED_DISPOSITION!r} result, and the other three terminal "
            f"dispositions are not results to hand to review")
    status = (evidence["independent"] or {}).get("verification_status")
    if status != 0:
        raise OperatorRefusal(
            f"this attempt's independent verification exited {status!r}; a "
            f"handoff retry preserves a VERIFIED result, and a recorded check "
            f"is not a passed one")
    # AND THE MANAGER IS ASKED, because the record is not an authority over
    # acts the manager owns. Review 2026-08-30T15:10:12Z [P0]: the retained
    # file is explicitly operator-editable and untrusted on read, and this
    # treated truthy members as proof that the freeze, the intake and the
    # retention had COMMITTED -- so an edited record could pass Work to review
    # while all three public readers reported absence.
    #
    # EDITABLE EVIDENCE MAY SAY WHAT TO LOOK UP AND MAY NOT MINT WHAT WAS
    # NEVER COMMITTED. Every fact below is replay-read from the manager's own
    # public surface and held against the record, before `_passed` is
    # reachable at all.
    _committed(store, evidence)
    # THE FAILURES THIS RETRY OWNS ARE THE ONES IT MAY SETTLE. Review
    # 2026-08-30T14:46:24Z [P0]: the retained record necessarily carries the
    # original pass or settlement failure, and `_ended_however` reports
    # `resolved` only when `unresolved` is empty -- so a retry that completed
    # both acts wrote a full pass and cleanup beside `resolved=False` and
    # exited 1 forever.
    #
    # HISTORY IS SET ASIDE STRUCTURALLY, not by matching this deployment's own
    # wording. The retained sentences are what was true BEFORE this retry; the
    # retry then re-performs the pass and the ending and writes what is true
    # AFTER. Nothing is erased on the strength of a prefix, and nothing
    # unrelated is quietly resolved either: `_ended_however` re-runs the
    # manager's own cleanup, so an unproved absence or an unsettled delivery
    # that is still true comes back on its own account rather than being
    # carried over on faith.
    historical = list(evidence["unresolved"])
    evidence["unresolved"] = []
    # THE PASS IS ALWAYS REPLAYED. Review 2026-08-30T15:41:53Z [P0]: this ran
    # only when the record held no pass, so a plausible projection typed into
    # the editable file skipped the authority call entirely -- an evidence
    # member had become an alternate authority fact.
    #
    # Replaying is both SAFE and NECESSARY: the pass carries this attempt's own
    # operation identity, so the authority returns its committed answer rather
    # than passing twice, and that answer is the only thing that can show the
    # pass happened. The file may identify what to replay and cannot prove it.
    answered = _passed(session, expect, review_route,
                       attempt_id=evidence["attempt_id"])
    recorded = evidence.get("review_pass")
    if recorded is not None and recorded != answered:
        raise OperatorRefusal(
            f"the retained record names a review pass {recorded!r} and the "
            f"authority replayed {answered!r}; a recorded projection is held "
            f"whole against the act it claims to be a record of")
    evidence["review_pass"] = answered
    _ended_however(store, port, adapter, evidence,
                   attempt_id=evidence["attempt_id"],
                   runtime_id=evidence["runtime_id"],
                   retention_policy_digest=retention_policy_digest)
    # AND IF IT DID NOT CONVERGE, THE HISTORY COMES BACK. A retry whose own
    # acts failed again has superseded nothing, and a record that had quietly
    # dropped the earlier account would be a shorter story about the same
    # unfinished attempt.
    if evidence["unresolved"]:
        evidence["unresolved"] = historical + [
            one for one in evidence["unresolved"] if one not in historical]
        evidence["resolved"] = False
    return evidence


# WHAT THE PASS SAYS IN THE AUTHORITY'S OWN JOURNAL. Fixed rather than
# composed from evidence: a comment is durable text on a Work other people
# read, and this deployment has exactly one thing to say with it.
PASS_COMMENT = ("passed by the supervised v12 dogfood operator after intake, "
                "independent verification and retention")

MAX_ABANDONMENT_REASON = 2000


# HOW DEEP A RETAINED TREE IS WALKED, AND HOW MANY ENTRIES, BEFORE THIS
# REFUSES TO KEEP WALKING. `workspaces.MAX_DEPTH` bounds the manager's own
# walks for the same reason and `MAX_SOURCE_ENTRIES` is this module's own
# stated ceiling: a walk with no limit is a walk somebody else decides the
# cost of, and this one runs over material a worker wrote.
MAX_KEPT_DEPTH = 64
MAX_KEPT_ENTRIES = MAX_SOURCE_ENTRIES

# THE ONE MEMBER THE DOCUMENTED USES ACT ON. `_derived` diffs `candidate`
# against the staged source and reruns the task's own command with it as
# `cwd`; the three siblings beside it are the worker's account and are
# collected rather than executed. So a retained proposal without this
# directory is one neither half of the acceptance can be performed on.
CANDIDATE_TARGET = "candidate"


def _readable(opened, name):
    """One regular file OPENED read-only and no-follow, then closed.

    W51473 review 2026-08-31T05:33:31Z [P1], and the reviewer is right twice
    over. The previous round opened and traversed DIRECTORIES and only
    `stat`ed everything else -- so a regular file at mode `000` inside a
    perfectly traversable tree passed a proof whose whole purpose is that the
    documented bytewise diff can read it. `filecmp.cmp` opens these files;
    `stat` does not.

    OPENING IS THE PROOF AND READING IS NOT NEEDED. A zero-byte file is a
    legitimate member -- the first live attempt's `change.patch` was exactly
    that -- so requiring a byte would refuse material the contract allows.
    What is in question is permission, and `os.open` answers it.
    """
    handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=opened)
    os.close(handle)


def _traversed(opened, depth, seen):
    """One directory opened, listed, descended, and its FILES opened.

    Each step needs exactly what one bad mode withholds: `os.open` with
    `O_DIRECTORY` needs READ on a directory, the descriptor-relative `os.stat`
    needs SEARCH, and opening a regular file needs READ on the file. Nothing
    here writes, creates or changes a mode.

    DESCRIPTOR-RELATIVE AND `O_NOFOLLOW`, the same idiom
    `workspaces._emptied` uses over the same kind of tree. A name resolved
    afresh at each step is a name something else can move between the check
    and the use, and a link followed here would be this operator proving
    something about material nobody retained.

    AND AN ENTRY THAT IS NEITHER IS REFUSED BY KIND rather than skipped. The
    independent diff reads regular files and walks directories; a link, a
    fifo, a socket or a device is not something it can read, and the manager's
    own copier refuses links at any depth -- so one here is a tree this
    operator should not be reporting as reviewable.
    """
    import stat as _stat

    for name in sorted(os.listdir(opened)):
        seen[0] += 1
        if seen[0] > MAX_KEPT_ENTRIES:
            raise _Lost(f"a retained tree holds more than "
                        f"{MAX_KEPT_ENTRIES} entries; this operator bounds "
                        f"the walk it performs over material a worker wrote")
        found = os.stat(name, dir_fd=opened, follow_symlinks=False)
        if _stat.S_ISREG(found.st_mode):
            _readable(opened, name)
            continue
        if not _stat.S_ISDIR(found.st_mode):
            raise _Lost(f"a retained tree holds {name!r}, which is neither a "
                        f"regular file nor a directory; the documented "
                        f"independent diff reads neither")
        if depth >= MAX_KEPT_DEPTH:
            raise _Lost(f"a retained tree is deeper than {MAX_KEPT_DEPTH} "
                        f"directories; this operator bounds the walk it "
                        f"performs over material a worker wrote")
        below = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                        dir_fd=opened)
        try:
            _traversed(below, depth + 1, seen)
        finally:
            os.close(below)


def _has_candidate(opened):
    """The fixed `candidate/` directory, proved present and a directory.

    W51473 review [P1], second half. The traversal alone admitted an EMPTY
    proposal root: it opens and lists successfully while the verification
    rerun has no `cwd` and the diff has nothing to compare. My own positive
    fixture was such a root, so the case that was supposed to keep the
    negative ones honest was locking the false positive in.

    ASKED AFTER THE TRAVERSAL, so a root this operator cannot read reports
    that rather than reporting a missing member it was never able to look for.
    """
    import stat as _stat

    try:
        found = os.stat(CANDIDATE_TARGET, dir_fd=opened,
                        follow_symlinks=False)
    except OSError:
        return False
    return _stat.S_ISDIR(found.st_mode)


def _kept(evidence):
    """Every retained artifact, proved to SUPPORT the documented acceptance.

    W51473's boundary in one function: "prove the retained public custody
    locator exists after command completion and supports the documented
    independent diff and verification rerun". Both of those are concrete acts.
    `_changed_paths` walks the candidate tree and compares files BY BYTES;
    the rerun executes the task's own command with `candidate` as its `cwd`.
    So what has to be true is that this operator can open the root, traverse
    everything under it, OPEN the files the diff would read, and find the one
    directory the rerun needs -- not merely that something is there.

    IT IS STILL NARROWER THAN RERUNNING THE VERIFICATION, deliberately. That
    already happened at `_derived`, over the same custody tree and before the
    ending; what this answers is whether the ending left it usable. Running a
    worker-influenced command a second time at the terminal boundary would be
    a new act rather than a proof about an old one.

    THE RECORD'S OWN LOCATOR IS WHAT IS OPENED, not a path recomposed here.
    It came from the intake receipt, and on the retry path `_committed` has
    already held it against the manager's own row.

    ONE SCHEME, THE SAME OWNER. `_proposal_root` is what `_derived` decodes
    with, and reusing it keeps "the locator the operator reads" and "the tree
    this deployment derived from" one path rather than two spellings.

    EVERY ARTIFACT IS ASKED ABOUT, and one failure does not stop the others:
    an operator reading this record is deciding what to do about their kept
    material, and "the first one failed" is less use than knowing which.
    """
    for one in evidence.get("custody") or ():
        try:
            place = _proposal_root(one["custody_locator"])
        except _Lost as why:
            _unresolved(evidence, str(why))
            continue
        try:
            opened = os.open(place,
                             os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        except OSError as failed:
            _unresolved(
                evidence,
                f"artifact {one['artifact_id']!r} was retained and its "
                f"custody locator {one['custody_locator']!r} is not a "
                f"directory this operator can open "
                f"({type(failed).__name__}); a keep nobody can open is not a "
                f"candidate anybody can review")
            continue
        # ONE DESCRIPTOR FOR BOTH QUESTIONS. Re-opening the root to ask the
        # second one would be asking about whatever answers to that name by
        # then, which is the resolve-twice defect this walk is built to avoid.
        try:
            _traversed(opened, 0, [0])
            if not _has_candidate(opened):
                _unresolved(
                    evidence,
                    f"artifact {one['artifact_id']!r} was retained and holds "
                    f"no {CANDIDATE_TARGET!r} directory; the documented "
                    f"independent diff compares that tree against the staged "
                    f"source and the verification rerun uses it as its "
                    f"working directory")
        except _Lost as why:
            _unresolved(evidence, f"artifact {one['artifact_id']!r}: {why}")
        except OSError as failed:
            _unresolved(
                evidence,
                f"artifact {one['artifact_id']!r} was retained and its "
                f"custody tree under {one['custody_locator']!r} cannot be "
                f"read ({type(failed).__name__}); the documented independent "
                f"diff opens every file in it")
        finally:
            os.close(opened)


def _ended_however(store, port, adapter, evidence, *, attempt_id, runtime_id,
                   retention_policy_digest):
    """The ending, run whatever happened -- and HONEST about what it can end.

    Review 2026-08-30T06:44:13Z [P0]. The previous `finally` only observed,
    while the record claimed the manager's own cleanup was attempted. It is
    attempted here, through the manager's own operation and never through a
    second deployment-owned destroy.

    AND THERE IS A STATE THIS SURFACE CANNOT END, which is recorded rather
    than worked around. `authorize_cleanup` is authorized by the INTAKE
    RECEIPT; `authorize_failed_start_cleanup` is authorized by the manager's
    own `runtime.start-failed` record; `authorize_refused_session_cleanup` by
    a refused session. An attempt whose runtime STARTED and whose worker then
    failed to answer has none of the three, so no public operation ends it --
    and inventing a destroy here would be exactly the second removal boundary
    a deployment must not grow. That is a MANAGER finding, filed as W44716,
    and until it lands such an attempt is `unresolved` with the runtime named
    so an operator can act on it.
    """
    from baton_v12.contracts import ContractRefusal as _Refusal
    from baton_v12.worker_manager import abandon_attempt, authorize_cleanup

    # ENDING A STARTED RUNTIME BEGINS BY STOPPING IT -- ON THE RECEIPT PATH.
    #
    # Review 2026-08-30T06:44:13Z [P0] required a stop on every post-start
    # path, because a lost conversation left the container running. Review
    # 2026-08-30T11:44:55Z [P0] then found the correction had gone one step
    # too far: on the RECEIPTLESS path the ending is now `abandon_attempt`,
    # whose whole ruling is FENCE BEFORE ANY RUNTIME CONTROL — and a stop this
    # deployment ordered first is one the manager cannot undo. That recreates
    # exactly the unsafe boundary W44716 was introduced to remove: the
    # authority may still consider the worker live while its runtime is
    # stopped.
    #
    # So the ordinary receipt-authorized cleanup keeps its established
    # quiescence path, and abandonment's composite owns its own fence and
    # removal order. Both paths still end a started runtime; only one of them
    # is this deployment's to begin.
    if evidence.get("intake_receipt") and evidence.get("quiescence") is None:
        try:
            stopped = adapter.stop({"runtime_id": runtime_id,
                                    "operation_id": f"quiesce:{attempt_id}"})
            evidence["quiescence"] = {"ordered": stopped.get("ordered"),
                                      "state": stopped.get("state"),
                                      "why": stopped.get("why")}
        except Exception as failed:                        # noqa: BLE001
            evidence["quiescence"] = {"ordered": False,
                                      "state": "unobserved",
                                      "why": type(failed).__name__}
            _unresolved(evidence, f"the runtime could not be ordered to stop "
                                  f"({type(failed).__name__})")
    if evidence.get("intake_receipt"):
        try:
            settled = authorize_cleanup(
                store, port, adapter, attempt_id=attempt_id,
                retention_policy_digest=retention_policy_digest)
            evidence["cleanup"] = {"cleanup": settled.get("cleanup"),
                                   "state": settled.get("state")}
            # THE TWO TERMINAL ENDINGS THIS DEPLOYMENT ASKED FOR, and which
            # one is expected is decided by the disposition the MANAGER
            # COMMITTED -- never by the grants and never by the record.
            #
            # W51473, and it is the half that makes the operand real. Swapping
            # the hard-coded literal for `retain` alone would have kept the
            # bytes and left the command unresolved forever: the manager ends
            # cleanup `retained` whenever anything is kept, deliberately,
            # because "retained" and "complete" are different endings and
            # reporting kept material as cleaned up would erase the reason it
            # still exists (`intake._settle`). This deployment used to treat
            # every ending but `complete` as a failure, so an INTENDED keep
            # read as a broken cleanup.
            #
            # SO THE EXPECTED ENDING IS DERIVED FROM THE COMMITTED DECISION.
            # `evidence["retention"]` is written from `decide_retention`'s own
            # answer on the ordinary path, and on the retry path `_committed`
            # has already held it against `retentions_of` before this is
            # reachable -- so an edited record cannot turn a discard into a
            # keep, and a retry cannot reinterpret somebody else's ending. A
            # retention that never committed leaves this `None`, which keeps
            # material for nobody and expects `complete`, which is exactly
            # what an attempt with no retention decision should expect.
            committed = (evidence.get("retention") or {}).get(
                "disposition")
            keeping = committed is not None and _keeps_material(committed)
            expected = "retained" if keeping else "complete"
            # POSITIVE ABSENCE IS STILL REQUIRED FOR BOTH, and that is the
            # ruled difference `retained` does NOT relax: the material staying
            # is a fact about custody, and the runtime being gone is a fact
            # about the engine. `retained` releases the lane precisely because
            # custody is a manager-owned sibling the worker never sees.
            # AND A KEEP IS PROVED ON THE DISK, AFTER THE REMOVAL, before it
            # can be called resolved.
            #
            # `_settle` discards the execution roots INSIDE the terminal
            # transaction, so this is the first moment "the candidate is still
            # there" is a fact rather than a plan. The manager already refuses
            # to journal a keep over material that is not there
            # (`OciAdapter.retain`), and this is the deployment's own half of
            # that: what an operator was promised is a locator THEY can open,
            # so it is asked of the filesystem here rather than inferred from
            # an ending. A keep whose locator is gone is unresolved, which is
            # the honest answer -- the ending happened and the thing it was
            # for did not survive.
            if keeping:
                _kept(evidence)
            if settled.get("cleanup") == expected \
                    and settled.get("state") == "absent" \
                    and not evidence["unresolved"]:
                evidence["resolved"] = True
            elif settled.get("cleanup") != expected:
                _unresolved(evidence,
                            f"cleanup ended {settled.get('cleanup')!r} with "
                            f"the runtime {settled.get('state')!r}, and this "
                            f"attempt's committed retention {committed!r} "
                            f"ends {expected!r}")
        except _Refusal as refused:
            _unresolved(evidence, f"the manager declined to end the attempt: "
                                  f"{refused.message}")
    else:
        # W44716 LANDED, so this is a real ending rather than a recorded gap.
        # An attempt whose runtime started and whose worker never answered has
        # no receipt, no start failure and no refusal -- and now has its own
        # public operation, authorized by an operator's explicit declaration.
        # The reason carried is this deployment's own account of why it is
        # declaring the attempt over; it reads no clock and no timer decides.
        try:
            ended = abandon_attempt(
                store, port, adapter, attempt_id=attempt_id,
                reason=_abandonment_reason(evidence),
                retention_policy_digest=retention_policy_digest)
            evidence["abandoned"] = {
                "fenced": bool(ended["fenced"].get("fenced")),
                "cleanup": ended["cleanup"].get("cleanup"),
                "state": ended["cleanup"].get("state")}
            if ended["cleanup"].get("cleanup") != "retained":
                _unresolved(evidence,
                            f"the abandonment ended "
                            f"{ended['cleanup'].get('cleanup')!r} with the "
                            f"runtime {ended['cleanup'].get('state')!r}")
        except _Refusal as refused:
            _unresolved(evidence, f"the manager declined to abandon the "
                                  f"attempt: {refused.message}")
    # THE LAST READ, and it belongs at the END of the ending. Review
    # 2026-08-30T11:44:55Z [P1]: an edit displaced this below an unconditional
    # return in another function, where it was unreachable and referred to
    # names that function does not have. It is the evidence an unsettled
    # abandonment needs in order to tell an operator what is still there.
    evidence["observed_after"] = _observed_after(adapter, runtime_id)


def _abandonment_reason(evidence):
    """Why THIS deployment is declaring the attempt over, in its own words.

    Composed from what was already recorded rather than restated, so the
    declaration an operator later reads in the journal is the same sentence
    the evidence carries. Bounded, because it is durable text.
    """
    return ("the dogfood operator declared this attempt abandoned: "
            + "; ".join(evidence["unresolved"] or ["no reason recorded"])
            )[:MAX_ABANDONMENT_REASON]


def _observed_after(adapter, runtime_id):
    """What the engine says about the runtime once the arc has finished.

    A READ AND NEVER A REMOVAL. Removing here would be a second destroy
    boundary beside the manager's own, which is the one thing a deployment
    must not grow; what this adds is that an unresolved evidence record says
    whether the container is still running rather than leaving an operator to
    go and look.
    """
    try:
        return dict(adapter.observe(runtime_id))
    except Exception as failed:                            # noqa: BLE001
        return {"state": "unobserved", "why": type(failed).__name__}


def _derived(custody_locator, task, source):
    """The diff and the verification, RECOMPUTED by this operator.

    NEITHER READS THE WORKER'S ACCOUNT. `change.patch` and `result.json` are
    the worker's convenience and are collected as evidence; what an operator
    acts on is this — the candidate tree custody holds, diffed against the
    staged source it was made from, and the task's own frozen command rerun
    OUTSIDE the container over that tree.

    THE LOCATOR IS THE RECEIPT'S. Review [P1]: it used to be derived from the
    adapter's private `_custody`, which is OCI's business and not a
    deployment's.
    """
    import subprocess

    # THE LOCATOR IS A URI, and this treated it as a path. W39358: the real
    # intake receipt carries `file:///...`, so `os.path.join` produced
    # `file:///...` and every real derivation died `FileNotFoundError` -- a
    # fault rather than the typed refusal a boundary owes. Only the one scheme
    # this deployment can read is accepted; anything else is refused by name
    # rather than guessed at.
    proposal = _proposal_root(custody_locator)
    candidate = os.path.join(proposal, "candidate")
    changed = sorted(_changed_paths(source, candidate))
    verified = subprocess.run(list(task["verification"]), cwd=candidate,
                              stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=900)
    return {"changed_paths": changed,
            "verification_argv": list(task["verification"]),
            "verification_status": verified.returncode,
            # THE SAME DECODED ROOT. Review 2026-08-30T19:44:14Z: this joined
            # below the raw `file://` STRING while the candidate above used
            # the decoded path, so every member answered absent and the record
            # reported an empty proposal with all four members present. One
            # decode, one root, both uses.
            "members_present": sorted(
                one for one in PROPOSAL_MEMBERS
                if os.path.exists(os.path.join(proposal, one)))}


def _proposal_root(custody_locator):
    """The ONE absolute local path a custody locator names.

    Decoded and validated once, and reused by every read below it. The first
    cut decoded it at one use and not the other, which is the shape of every
    two-spellings defect in this dossier.
    """
    if type(custody_locator) is not str \
            or not custody_locator.startswith("file://"):
        raise _Lost(f"custody answered {custody_locator!r} and this operator "
                    f"reads a local `file://` locator; a scheme it cannot open "
                    f"is not a tree it can independently derive")
    place = custody_locator[len("file://"):]
    if not os.path.isabs(place):
        raise _Lost(f"custody answered {custody_locator!r}, whose path is not "
                    f"absolute; a proposal root this operator cannot name "
                    f"exactly is not one it can derive from")
    return place


def _changed_paths(source, candidate):
    """Which staged files the candidate differs from, by BYTES.

    Not by the worker's list and not by a digest the worker computed: the two
    trees are on this host and comparing them is the one derivation nothing
    inside the container can influence.
    """
    import filecmp

    found = set()
    for base, _directories, files in os.walk(source):
        for name in files:
            relative = os.path.relpath(os.path.join(base, name), source)
            theirs = os.path.join(candidate, relative)
            if not os.path.isfile(theirs) or not filecmp.cmp(
                    os.path.join(base, name), theirs, shallow=False):
                found.add(relative)
    for base, _directories, files in os.walk(candidate):
        for name in files:
            relative = os.path.relpath(os.path.join(base, name), candidate)
            if not os.path.isfile(os.path.join(source, relative)):
                found.add(relative)
    return found


def _unresolved(evidence, why):
    """An attempt whose required proof was not obtained, said out loud."""
    evidence["resolved"] = False
    evidence["unresolved"].append(why)
    return evidence


def _configured_group(store):
    from baton_v12.worker_manager import configured_workspace_group

    return configured_workspace_group(store)


def _claim_receipt(claimed):
    """The claim's receipt digest, DERIVED from the authority's own result.

    Review 2026-08-30T06:35:56Z [P0]. There is no placeholder branch, and that
    is the correction: a manifest that could fall back to a well-formed
    all-zero digest was one an operator would read as evidence. `submit_claim`
    answers the authority's exact assignment, claim event and decision, and
    the receipt digest is over those three — which is what makes it a digest
    OF the claim rather than a value this deployment chose.
    """
    from baton_v12.contracts import digest

    return digest(_claim_facts(claimed))


def _claim_event(claimed):
    """The authority's own claim event sequence, or a refusal."""
    return _claim_facts(claimed)["claim_event"]


def _claim_facts(claimed):
    """The three facts `submit_claim` answers, held before either is used."""
    if type(claimed) is not dict:
        raise OperatorRefusal(
            f"the claim answered a {type(claimed).__name__} rather than the "
            f"authority's closed result; an assignment manifest is bound to "
            f"that result and to nothing this deployment composed")
    missing = sorted(one for one in ("assignment", "claim_event", "decision")
                     if one not in claimed)
    if missing:
        raise OperatorRefusal(
            f"the claim result names none of {', '.join(missing)}; an "
            f"assignment manifest carries the authority's evidence and this "
            f"deployment does not invent the parts it was not given")
    return {one: claimed[one]
            for one in ("assignment", "claim_event", "decision")}


def _disposition_of(spoken):
    """What the worker SAID it did, out of the `work` answer and nowhere else."""
    for one in spoken["answers"]:
        if one.get("operation") == "work":
            body = one.get("answer") or {}
            return body.get("disposition")
    return None


# EXACTLY WHAT A GRANTS FILE IS. Held as a closed set for the same reason
# every other document here is: an operator who misspells a member is told,
# and a member this build does not read cannot sit in a file looking like it
# was honoured.
GRANT_MEMBERS = (
    "engine", "attempt_id", "offer_id", "source", "task_path", "storage",
    "launch_home", "control_store", "authority_store", "incarnation",
    "credential_home", "credential_slots", "credential_profile",
    "image_digest", "network", "review_route", "retention_disposition",
    "work_ref", "participant", "generation", "now", "policies",
    "record_binding", "assignment_contract", "human_contract",
    "role_instructions_digest", "runtime_profile_digest", "toolchain_digest",
    "adapter_digest", "adapter_name", "labels", "retention_policy_digest")


def read_grants(place):
    """The operator's decisions, read once and held to the closed set.

    SEPARATE FROM `preflight` ON PURPOSE. This holds the FILE -- is it a
    document, are these the members this build reads -- and `preflight` holds
    the VALUES. Two owners because they answer to two different people: this
    one to whoever wrote the file, that one to whoever granted what is in it.
    """
    with open(place, "rb") as reading:
        body = reading.read()
    try:
        given = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as broken:
        raise OperatorRefusal(
            f"the grants file is one JSON document and this one is not "
            f"({type(broken).__name__})")
    if type(given) is not dict:
        raise OperatorRefusal(
            f"the grants file is one JSON object; this is a "
            f"{type(given).__name__}")
    missing = sorted(one for one in GRANT_MEMBERS if one not in given)
    extra = sorted(one for one in given if one not in GRANT_MEMBERS)
    if missing or extra:
        raise OperatorRefusal(
            "a grants file names exactly what this operator was given"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    # §13 AT THE FILE BOUNDARY TOO. A grants file is a durable surface an
    # operator edits by hand, and the one place a bearer is most likely to be
    # pasted "just for a moment". Refusing here is cheaper than discovering it
    # in the evidence record afterwards.
    try:
        check_no_durable_secret(given, "a dogfood grants file")
    except ContractRefusal as refused:
        raise OperatorRefusal(
            f"this grants file will not be used: {refused.message}")
    return given


def compose(given, *, session, bearer, credential_delivery, open_store,
            adapter_of, run, open_channel):
    """One attempt, from a grants document and the launcher's capabilities.

    WHAT IS IN THE FILE AND WHAT IS NOT is the whole shape of this function.
    Identities, paths and names come from the file, because an operator
    decides them and a durable record of them is exactly what the acceptance
    asks for. The SESSION and the BEARER arrive as operands, because §13 keeps
    the one deliberate secret off durable surfaces and a session is a minted
    capability rather than a value anybody can write down.

    THE STORE IS OPENED BY THE LAUNCHER, for the same reason: a control store
    is the manager's, and a deployment that opened one itself would be
    choosing an incarnation identity that belongs to whoever runs the manager.
    The credential delivery is a capability too, and arrives the same way.
    """
    from baton_v12.authority import claim_signature
    from baton_v12.worker_manager import AuthorityPort

    store = open_store(given["control_store"])
    # THE AUTHORITY'S OWN DERIVATION, passed rather than wrapped. A lambda
    # around it here would be a second place the claim signature is spelled.
    port = AuthorityPort(session, claim_signature)
    return run_dogfood_task(
        engine=given["engine"], run=run, open_channel=open_channel,
        store=store, port=port, session=session, adapter_of=adapter_of,
        review_route=given["review_route"],
        attempt_id=given["attempt_id"], offer_id=given["offer_id"],
        source=given["source"], task_path=given["task_path"],
        storage=given["storage"], launch_home=given["launch_home"],
        credential_delivery=credential_delivery,
        image_digest=given["image_digest"], network=given["network"],
        work_ref=given["work_ref"], participant=given["participant"],
        generation=given["generation"], now=given["now"],
        policies=given["policies"], record_binding=given["record_binding"],
        assignment_contract=given["assignment_contract"],
        human_contract=given["human_contract"],
        role_instructions_digest=given["role_instructions_digest"],
        runtime_profile_digest=given["runtime_profile_digest"],
        toolchain_digest=given["toolchain_digest"],
        adapter_digest=given["adapter_digest"],
        adapter_name=given["adapter_name"], labels=given["labels"],
        retention_policy_digest=given["retention_policy_digest"],
        retention_disposition=given["retention_disposition"],
        bearer=bearer)


def _held_grants(given):
    """Every grant judgeable WITHOUT a capability, held before one is built.

    W51476 review [P1]. `main` builds the ordinary capabilities before
    `compose` runs, and the real builder opens two stores and materializes the
    attempt's credential slot -- so every hold inside `run_dogfood_task` was
    behind an outward act. This is the same set of holds, applied where
    nothing has happened yet.

    IT IS NOT A SECOND SET OF RULES. `frozen_task` and `preflight` are the
    owners `run_dogfood_task` uses, called here with the same operands; a
    check written out again would be a second thing to keep in agreement.
    Both stay where they were, because a direct caller of `run_dogfood_task`
    is not reached by this and `input_manifest`'s hold answers a different
    question -- a document changed after it was read.

    READING THE OPERATOR'S OWN TASK FILE IS NOT A SIDE EFFECT. It creates
    nothing, opens no store, touches no credential home and starts no engine;
    an operator whose task file is missing learns it here rather than after a
    credential exists.
    """
    preflight(task=frozen_task(given["task_path"]),
              policies=given["policies"],
              worker_image_digest=given["image_digest"],
              toolchain_digest=given["toolchain_digest"],
              runtime_profile_digest=given["runtime_profile_digest"],
              role_instructions_digest=given["role_instructions_digest"],
              record_binding=given["record_binding"],
              network=given["network"],
              review_route=given["review_route"],
              retention_disposition=given["retention_disposition"],
              human_contract=given["human_contract"])


def main(argv, *, capabilities, retry_capabilities=None):
    """The documented command, and it answers a process exit status.

    ONE INJECTED THING, and it is a FUNCTION OF THE GRANTS. The seven
    capabilities cannot be built before the grants are read -- the authority
    store, the control store and the credential home are all named in the file
    -- so what is injected is the launcher that builds them, not the built
    things. `_launched` is the real one; a test supplies its own and neither
    has to pretend the other's boundary does not exist.

    `0` IS A RESOLVED ATTEMPT AND NOTHING ELSE. An attempt that ran but could
    not prove its ending exits non-zero even though nothing raised, because an
    operator scripting this reads the status before the file and a supervised
    pilot that reported success for an unproved ending would be the one
    failure mode this deployment must not have.

    AND A POST-START FAULT STILL LEAVES A FILE. Approver ruling item 8: the
    fault propagates, because an implementation defect is not an attempt
    outcome -- but the record of the attempt that was running when it happened
    is written first.
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="dogfood_operator",
        description="Run one supervised v12 dogfood attempt.")
    parser.add_argument("--grants", required=True,
                        help="the JSON document of operator decisions")
    parser.add_argument("--evidence", required=True,
                        help="where the durable evidence record is written")
    # NAMED BY THE ONE PUBLIC PARSER. Review 2026-08-30T14:36:46Z [P1]: a
    # private pre-parser stripped this before `main` ever saw it, so
    # `--help` listed two operands while the launcher refused without a
    # third. An operand a command requires and does not name is an operand an
    # operator discovers by failing.
    parser.add_argument("--credential-file",
                        help="path to the provider credential this attempt "
                             "delivers; read once into memory, never written "
                             "back, and never a grants member because a "
                             "grants file is a durable surface")
    parser.add_argument("--retry-handoff", action="store_true",
                        help="retry ONLY the pass and settlement of an "
                             "attempt whose completed, independently verified "
                             "result is already recorded in --evidence; runs "
                             "no worker, starts no runtime and restages "
                             "nothing")
    options = parser.parse_args(argv)
    given = read_grants(options.grants)
    if options.retry_handoff:
        # APPROVER RULING M46985, REACHABLE. Review [P0]: the narrow retry
        # existed as a function nobody could call -- an operator whose pass
        # failed had no documented way to perform it, and exact whole-attempt
        # replay deliberately refuses at staging, so there was no way at all.
        #
        # IT READS THE RETAINED RECORD, which is the point: the original
        # process is gone, so the trusted result is whatever this deployment
        # durably wrote down. The capabilities are rebuilt fresh from the same
        # grants, so the pass and settlement carry the SAME identities and the
        # authority and the manager replay rather than repeat.
        # BOUND BEFORE A CAPABILITY IS BUILT, because building one is already
        # an outward act: it opens stores and touches the credential home.
        if retry_capabilities is None:
            raise OperatorRefusal(
                "this launcher supplies no retry capability path; a retry "
                "adopts an existing delivery and allocates nothing, so it is "
                "not the ordinary builder with a flag")
        return _retried(read_evidence(options.evidence), given,
                        retry_capabilities, options.evidence)
    # HELD BEFORE A CAPABILITY IS BUILT, because building one is already an
    # outward act -- the retry branch above says so in those words and the
    # ordinary branch did not do it.
    #
    # W51476 review [P1]. The shared hold was correct at both places it
    # reached and the documented command reached it too late: `capabilities`
    # is called HERE, and the real builder `_launched` opens the authority,
    # opens the control store and calls `CredentialHome.materialize` before
    # `compose` ever reaches `run_dogfood_task`'s preflight. So W39364's exact
    # malformed contract still materialized the attempt's credential slot
    # before anything refused it -- which is the observed defect, one layer
    # further out than the layer I fixed.
    #
    # MY OWN ARC CASE DID NOT COVER THIS and my report said it did. It called
    # `run_dogfood_task` directly with an already-built delivery and spied on
    # inner-arc operations; `assignment_workspace` is a workspace allocation
    # and is not credential materialization. The claim was wrong.
    #
    # THIS BOUNDARY IS PURE. It reads the operator's own task file and applies
    # the same holds `run_dogfood_task` applies -- no store, no home, no
    # engine. The inner preflight STAYS: a direct caller of `run_dogfood_task`
    # is not reached by this, and the composer's hold is a different question
    # again (a document changed after it was read).
    _held_grants(given)
    built = capabilities(given)
    closing = built.pop("closing", ())
    try:
        evidence = compose(given, **built)
    except BaseException as failed:                        # noqa: BLE001
        carried = getattr(failed, "dogfood_evidence", None)
        if carried is not None:
            write_evidence(carried, options.evidence)
        raise
    finally:
        # CLOSED ON EVERY PATH, including the one that propagates a fault: a
        # command that faulted still held two durable handles.
        for release in closing:
            release()
    # WRITTEN WHATEVER HAPPENED, because an unresolved attempt is exactly the
    # one an operator most needs the record of.
    write_evidence(evidence, options.evidence)
    return 0 if evidence["resolved"] else 1


def read_evidence(place):
    """A retained evidence record, read back and held to the same closed set.

    THE SAME HOLD AS THE WRITE, because a record read back is as untrusted as
    any other document that crossed a boundary -- it has been on a disk an
    operator can edit, and a retry that believed an edited one would hand on a
    result nobody produced.
    """
    # BOUNDED AT THE READ, not after it. Reading a file of unknown size into
    # memory and then measuring it is a ceiling that admits the thing it is
    # supposed to refuse.
    with open(place, "rb") as reading:
        body = reading.read(MAX_EVIDENCE_BYTES + 1)
    if len(body) > MAX_EVIDENCE_BYTES:
        raise OperatorRefusal(
            f"the retained evidence is larger than the "
            f"{MAX_EVIDENCE_BYTES} bytes this operator reads")
    try:
        record = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as broken:
        raise OperatorRefusal(
            f"the retained evidence is one JSON document and this one is not "
            f"({type(broken).__name__})")
    if type(record) is not dict:
        raise OperatorRefusal(
            f"the retained evidence is one JSON object; this is a "
            f"{type(record).__name__}")
    # THE SAME TWO HOLDS THE WRITE APPLIES, and for a stronger reason on this
    # side. Review [P0]: a bearer inserted into an ALLOWED member of an edited
    # record would reach authority and manager operands and every refusal
    # surface composed from them, long before the final writer got another
    # chance to reject it. A file that has been on a disk an operator can edit
    # is read with the boundary the writer used, not a weaker one.
    try:
        check_no_durable_secret(record, "a retained dogfood evidence record")
    except ContractRefusal as refused:
        raise OperatorRefusal(
            f"this retained evidence will not be used: {refused.message}")
    missing = sorted(one for one in EVIDENCE_MEMBERS if one not in record)
    extra = sorted(one for one in record if one not in EVIDENCE_MEMBERS)
    if missing or extra:
        raise OperatorRefusal(
            "a retained evidence record is exactly the members this operator "
            "composes"
            + (f"; missing {', '.join(missing)}" if missing else "")
            + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return record


# WHAT A RETRY MUST FIND UNCHANGED BETWEEN THE RECORD AND THE GRANTS. Each is
# a fact the pass or the settlement is composed from, so a disagreement is two
# different attempts being spliced rather than one being resumed.
_RETRY_BINDING = ("attempt_id", "work_ref", "participant", "generation",
                  "worker_image_digest", "network", "review_route",
                  "retention_policy_digest")


def _bound(evidence, given):
    """Hold the retained record to the grants BEFORE anything outward happens.

    Review 2026-08-30T14:46:24Z [P0]: `_retried` opened stores, allocated
    roots and built an adapter before comparing anything, and even then took
    the assignment from the grants while taking the operation id, the runtime
    and the settlement attempt from the evidence. A closed, valid record could
    therefore be paired with another assignment's grants and the mismatch
    would surface, if at all, as a manager refusal about something else.

    THIS RUNS FIRST, and it compares every identity the handoff is composed
    from -- not `attempt_id` alone, because an attempt name that matched while
    the work, participant or generation did not would still be two attempts.
    """
    named = {"attempt_id": given.get("attempt_id"),
             "work_ref": given.get("work_ref"),
             "participant": given.get("participant"),
             "generation": given.get("generation"),
             "worker_image_digest": given.get("image_digest"),
             "network": given.get("network"),
             "review_route": given.get("review_route"),
             "retention_policy_digest": given.get(
                 "retention_policy_digest")}
    disagreed = [one for one in _RETRY_BINDING
                 if evidence.get(one) != named[one]]
    if disagreed:
        raise OperatorRefusal(
            f"the retained evidence and these grants disagree on "
            f"{', '.join(disagreed)}; a handoff retry resumes ONE attempt, "
            f"and a record that names another is not this attempt's result "
            f"however well formed it is")
    # THE RETENTION DISPOSITION IS HELD TOO, and against the COMMITTED
    # decision rather than beside the flat members above.
    #
    # W51473. It is not an evidence member of its own -- what the record
    # carries is `retention.disposition`, the manager's own committed answer --
    # so the generic loop cannot reach it, and leaving it out would leave the
    # one operand that decides whether the ending is `retained` or `complete`
    # free to differ between the run and its retry. A retry granted `retain`
    # over an attempt that committed a discard would then expect an ending the
    # manager will never produce, and one granted a discard over a committed
    # keep would call a `retained` ending broken.
    #
    # A RETENTION THAT NEVER COMMITTED IS NOT A DISAGREEMENT. `retry_handoff`
    # refuses that record separately and for a better reason -- there is no
    # result to hand on -- and duplicating the refusal here would report the
    # grants as wrong when what is missing is the decision.
    granted = given.get("retention_disposition")
    committed = (evidence.get("retention") or {}).get("disposition")
    if committed is not None and granted != committed:
        raise OperatorRefusal(
            f"these grants ask for retention {granted!r} and this attempt "
            f"committed {committed!r}; a handoff retry finishes the ending "
            f"the manager already decided and does not redecide what happens "
            f"to the material")
    return evidence


def _retried(evidence, given, capabilities, place):
    """The narrow retry, over freshly built capabilities and a retained record.

    NOTHING WORKER-SIDE IS CONSTRUCTED. `retry_handoff` needs the store, the
    port, the session and an adapter to end the attempt with; it needs no
    engine runner and no channel, because it runs no container and opens no
    conversation. What is rebuilt is exactly what the pass and the settlement
    need.
    """
    from baton_v12.worker_manager import AuthorityPort
    from baton_v12.authority import claim_signature

    # BOUND FIRST, INSIDE, so no caller can reach the outward acts by calling
    # this directly. Review [P0]: the mismatch has to be refused before a
    # store, a workspace, a credential delivery or an adapter is touched.
    _bound(evidence, given)
    built = capabilities(evidence, given)
    store, session, adapter = built["store"], built["session"], built["adapter"]
    # CLOSED WHATEVER HAPPENS. Review 2026-08-30T17:13:10Z [P1]: `_for_retry`
    # opens an authority and a control store and this closed neither, so a
    # command that ran a retry left two SQLite handles behind -- and a handle
    # this process still holds is a lock the next incarnation waits on.
    try:
        answered = retry_handoff(
            store, AuthorityPort(session, claim_signature), session, adapter,
            evidence,
            expect={"work_ref": dict(given["work_ref"]),
                    "participant": given["participant"],
                    "generation": given["generation"]},
            review_route=given["review_route"],
            retention_policy_digest=given["retention_policy_digest"])
    finally:
        for closing in built.get("closing", ()):
            closing()
    write_evidence(answered, place)
    return 0 if answered["resolved"] else 1


# -- THE LAUNCHER: the deployment's own half of the world ---------------------
#
# WHY THIS IS HERE AND NOT IN THE PACKAGE. Every outward act in the Worker
# Manager crosses an injected capability, and the thing that actually spawns a
# process belongs to the DEPLOYMENT. `worker_entry` says so about the channel
# in as many words -- "this is the object the package deliberately does not
# contain". This module is the deployment, so this is where that object lives.
#
# Review 2026-08-30T12:40:47Z [P0] is exactly the gap between having written
# every rule and never having written the half that runs them: the command was
# documented, the composition was tested, and executing the documented line
# defined some functions and exited 0.


class _Channel:
    """One `docker exec` process, driven as a framed stream.

    STDERR IS DRAINED BY A THREAD from the moment the process starts. A
    container that writes more diagnostics than a pipe buffer holds would
    otherwise block in `write` while this waited on stdout, and the two would
    wait for each other -- a hang indistinguishable from a worker that stopped
    answering.

    NOTHING HERE INTERPRETS A FRAME. The framing, the vocabulary and every
    rule about what an answer means belong to `worker_entry`; this owns a pipe.
    """

    def __init__(self, argv, *, seconds):
        import subprocess
        import threading

        self._seconds = seconds
        self._process = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE)
        self._errors = []
        # DRAINED AND DISCARDED. Review W39357 [P1]: provider diagnostics that
        # reach a durable surface are a credential disclosure, and the only
        # reason to hold these bytes at all is to keep the pipe from filling.
        self._pump = threading.Thread(target=self._drain, daemon=True)
        self._pump.start()

    def _drain(self):
        # KEPT ONLY AS A BOUNDED WINDOW for the transport's own ending
        # document, which names `stderr` and holds it to text. It is never
        # written anywhere durable: `_ended_however` records the transport's
        # VOCABULARY, and W39357's finding is that provider diagnostics on a
        # durable surface are a credential disclosure.
        for chunk in iter(lambda: self._process.stderr.read(4096), b""):
            if len(self._errors) < self._KEEP:
                self._errors.append(chunk)

    def send(self, payload):
        self._process.stdin.write(payload)
        self._process.stdin.flush()

    def receive(self, count):
        return self._process.stdout.read1(count)

    def close_input(self):
        if not self._process.stdin.closed:
            self._process.stdin.close()

    # A FEW CHUNKS, because the ending's `stderr` is bounded at the transport
    # and an unbounded buffer here would be an unbounded read driven by the
    # container.
    _KEEP = 8

    def finish(self):
        """The session's ending, as the DOCUMENT the transport reads.

        W39358: this answered a bare integer, and `worker_entry._finished`
        requires `{status, stderr}` -- so every real conversation this
        deployment ever held ended `lost` with "the session's ending could not
        be read", including the one the arc gate reported as an unauthorized
        provider dry run. The worker had answered; this could not say so.
        """
        self.close_input()
        status = self._process.wait(timeout=self._seconds)
        self._pump.join(self._seconds)
        self._process.stdout.close()
        self._process.stderr.close()
        return {"status": status,
                "stderr": b"".join(self._errors).decode("utf-8", "replace")}


def _engine_run(argv, *, seconds=None):
    """The engine port's run operation, over a real process.

    The STREAMS ARE RETURNED because `EnginePort` reads them -- a container id
    comes back on stdout and a refusal on stderr -- and they are the engine's
    own text about its own act, not the worker's or the provider's.
    """
    import subprocess

    # THE MANAGER'S OWN DEADLINE, HONOURED. W39358's real-authority gate found
    # this: W43975's custody act refuses an engine capability it cannot bound,
    # and this runner took no `seconds` at all -- so every ending that settles
    # through a directory act was unreachable from the documented command. The
    # default stands for the calls that name no deadline.
    finished = subprocess.run(argv, capture_output=True,
                              timeout=600 if seconds is None else seconds)
    return {"status": finished.returncode,
            "stdout": finished.stdout.decode("utf-8", "replace"),
            "stderr": finished.stderr.decode("utf-8", "replace")}


def _launch_operands(attempt_id, task):
    """WHAT THIS DEPLOYMENT LAUNCHES WITH, in one place.

    W47225 review [P0]: adoption now requires the exact canonical bytes this
    component would have written, which means the retry has to name the same
    session, contract and role the ordinary arc did. Two spellings of that
    would be a delivery the retry could never adopt, discovered only after a
    handoff had already failed once.
    """
    return {"attempt_id": attempt_id, "session": f"session-{attempt_id}",
            "contract": task["instructions"], "role": "implementer"}


def _for_retry(evidence, given, *, provider=None):
    """Only what the PASS and the SETTLEMENT need, and nothing that allocates.

    Review 2026-08-30T14:46:24Z [P0]. The retry rebuilt the ordinary launcher,
    which always calls `CredentialHome.materialize` -- and that operation
    deliberately refuses a pre-existing root, because an existing root is a
    live delivery or an orphan to be ADOPTED and never overwritten. The
    approved retry case is precisely a refused pass after committed intake,
    where the assignment is still live and the credential root therefore still
    exists, so the retry could never reach the pass it promises. It also
    called `assignment_workspace`, an allocating, mode-adopting filesystem
    operation, in a mode that promises only a pass and a settlement.

    SO NOTHING HERE CREATES ANYTHING. The credential lifecycle is ADOPTED from
    the manager's own durable state record; the assignment roots are PROVED to
    exist and are not allocated or re-adopted; and no engine runner, no
    channel and no provider callback is constructed at all, because a retry
    runs no container and opens no conversation.
    """
    from baton_v12.authority import Authority
    from baton_v12.worker_manager import ControlStore, credentials, launch
    from baton_v12.worker_manager.oci import EnginePort, OciAdapter

    del provider
    authority = Authority.open(given["authority_store"])
    opened = [authority.dispose]
    try:
        session = DeploymentSession(authority.session(given["participant"]))
        store = ControlStore.open(given["control_store"],
                                  incarnation=given["incarnation"],
                                  clock=_now)
        opened.append(store.close)
        home = credentials.CredentialHome(given["credential_home"])
        recorded = home.read_state(given["attempt_id"])
        # ADOPTED OR ABSENT, never made. A delivery this manager already wrote is
        # recovered on the exact agreement `adopt` requires; an attempt that never
        # had one has none to recover, and inventing one here would be delivering
        # a credential during a retry that runs no worker.
        delivery = (home.adopt(recorded, attempt_id=given["attempt_id"],
                               runtime_id=evidence["runtime_id"],
                               workspace_group=_configured_group(store))
                    if recorded is not None else None)
        return {"store": store, "session": session,
                # WHAT THIS BUILDER OPENED, so the caller can close it. It opens
                # two durable handles and a caller that could not release them
                # would be leaking whatever a retry costs, every retry.
                "closing": (store.close, authority.dispose),
                "adapter": OciAdapter(
                    given["engine"], EnginePort(_engine_run),
                    identity={"image_digest": given["image_digest"],
                              "profile_digest": given["runtime_profile_digest"],
                              "policy_digest": given["policies"]["policy_digest"],
                              "adapter_digest": given["adapter_digest"]},
                    # `dict(...)` exactly as the ordinary launcher does: the
                    # adapter's boundary takes built-in documents, and the nominal
                    # type the manager answers with carries behaviour. That this
                    # flattening loses the proved identity is the standing [P1],
                    # recorded and not papered over here.
                    # THE MANAGER'S OWN ANSWER, unflattened. `_roots` adopts a
                    # nominal `AllocatedRoots` rather than re-deriving it, so
                    # the proof `adopted_assignment_workspace` performed
                    # survives to the adapter's use instead of being reduced
                    # to path strings this deployment asserts something about.
                    assignment_roots=_proved_roots(given),
                    posture="execution",
                    mounts=[], workspace_group=_configured_group(store),
                    # W47225: THE LAUNCH ROOT IS ADOPTED, NOT LEFT BEHIND, AND
                    # ITS ABSENCE IS A CONTRADICTION HERE. This passed `None`, so
                    # `authorize_cleanup` could remove the runtime while the
                    # adapter reported the launch delivery `not-delivered` and the
                    # root stayed on disk with nothing that would come back for
                    # it. `launch.adopt` proves the delivery this manager already
                    # made; this deployment reconstructs nothing.
                    #
                    # `None` is an ordinary answer FOR THE COMPONENT -- some
                    # attempts have no launch delivery -- and a contradictory one
                    # for THIS caller, whose retained evidence says the runtime
                    # started, and a runtime only starts after `materialize`
                    # completes. So the refusal is here, where the contradiction
                    # is, rather than in a component that cannot know it.
                    launch_delivery=_adopted_launch(evidence, given),
                    credential_delivery=delivery,
                    network=given["network"], interactive=True)}
    except BaseException:                                # noqa: BLE001
        _unwinding(opened)
        raise


def _adopted_launch(evidence, given):
    """The delivery the ordinary attempt made, and never `None` here."""
    from baton_v12.worker_manager import launch

    adopted = launch.adopt(
        given["launch_home"],
        **_launch_operands(given["attempt_id"], frozen_task(given["task_path"])))
    if adopted is None:
        raise OperatorRefusal(
            f"attempt {given['attempt_id']!r} has no launch delivery to "
            f"adopt, and its retained evidence says a runtime started -- "
            f"which only happens after one was materialized. Ending it with "
            f"no delivery would report `not-delivered` for a root that was "
            f"really made, which is the settlement this Work exists to stop")
    return adopted


def _proved_roots(given):
    """The attempt's existing roots, PROVED BY THE MANAGER and not here.

    The name is unchanged on purpose: what moved is WHERE the proof lives,
    not what this function is for.

    W39358 review [P1]. This module's own version derived the paths, checked
    them, and then handed them to an adapter that opened them again -- a
    deployment-side check followed by a later use, which is both a second
    spelling of allocation's containment rule and a check-then-open race.

    `workspaces.adopted_assignment_workspace` is that rule where it belongs:
    read-only, allocating nothing, changing no mode or group, and answering
    the same `AllocatedRoots` an allocation would -- so the adapter receives
    roots whose provenance is the manager's rather than this deployment's
    assertion about them.
    """
    from baton_v12.worker_manager import workspaces

    try:
        return workspaces.adopted_assignment_workspace(given["storage"],
                                                       given["attempt_id"])
    except ContractRefusal as refused:
        raise OperatorRefusal(
            f"attempt {given['attempt_id']!r} has no roots this manager will "
            f"adopt: {refused.message}")


def _unwinding(opened):
    """Release what a half-built capability set already opened, then re-raise.

    W39358 review 2026-08-30T18:54:12Z [P1]. A builder answers `closing` so
    its caller can release the handles it opened -- but only if it RETURNS. An
    authority opened before a control store that then fails is an authority
    nobody disposes, because the bundle carrying its release never exists.

    Construction unwinds locally for the same reason `materialize` tears its
    own root down: the caller cannot clean up what it was never handed.
    """
    for release in reversed(opened):
        try:
            release()
        except BaseException:                              # noqa: BLE001
            # A FAILING RELEASE MUST NOT HIDE THE FAULT that caused the
            # unwind. What is being reported is why construction stopped.
            pass


def _now():
    """This deployment's own clock, in the manager's own spelling.

    Injected rather than ambient for the reason the manager takes it as an
    operand: a store that read the wall clock itself would be dating its own
    evidence, and a deployment is the thing that decides what time it is here.
    """
    import datetime

    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.") + f"{datetime.datetime.now().microsecond // 1000:03d}Z"


def _minted_bearer():
    """One use, minted here, and never written down.

    NOT A GRANT MEMBER and not an environment variable: §13 keeps the one
    deliberate secret off every durable surface, and both of those are durable
    surfaces. It exists for the length of this process.
    """
    import secrets as _entropy

    return _entropy.token_urlsafe(32)


def _launched(given, *, credential_provider):
    """Every capability the arc needs, built from what the operator granted.

    THE ONE THING THIS CANNOT BUILD is the credential provider: live provider
    authorization is W39364's operator gate, so it arrives as an operand and
    this launcher never learns where the material came from.
    """
    from baton_v12.authority import Authority
    from baton_v12.worker_manager import ControlStore, credentials
    from baton_v12.worker_manager.oci import EnginePort, OciAdapter

    authority = Authority.open(given["authority_store"])
    # CONSTRUCTION UNWINDS LOCALLY. The bundle below carries
    # `closing`, but only if it is RETURNED: an authority opened
    # before a control store that then fails is an authority
    # nobody disposes, because the thing carrying its release
    # never exists. The caller cannot clean up what it was never
    # handed.
    opened = [authority.dispose]
    try:
        session = DeploymentSession(authority.session(given["participant"]))
        # OPENED ONCE, HERE, because choosing an incarnation identity is the
        # deployment's act and `compose` should not be making it twice. The
        # workspace group is read off this manager's OWN record rather than
        # composed, which is the sequence a deployment performs.
        # THE CLOCK IS THE DEPLOYMENT'S, and it is required rather than defaulted
        # -- found by the positive launcher case, which is the first thing ever to
        # run this construction. `ControlStore.open` takes it keyword-only and
        # this passed none, so the documented command could not have opened a
        # store at all.
        store = ControlStore.open(given["control_store"],
                                  incarnation=given["incarnation"],
                                  clock=_now)
        opened.append(store.close)
        group = _configured_group(store)
        home = credentials.CredentialHome(given["credential_home"])
        delivery = home.materialize(
            credentials.resolved_delivery(given["credential_slots"],
                                          profile=given["credential_profile"]),
            attempt_id=given["attempt_id"],
            # W52800: the slot's reader group is a grant, and this launcher
            # already read the one nominal capability for the adapter below.
            # One lookup, both halves.
            workspace_group=group,
            credential_provider=credential_provider)

        def adapter_of(*, engine, run, image_digest, network, labels, roots,
                       declared, launch, credential_delivery,
                       input_manifest_digest):
            return OciAdapter(
                engine, EnginePort(run),
                identity={"image_digest": image_digest,
                          "profile_digest": given["runtime_profile_digest"],
                          "policy_digest": given["policies"]["policy_digest"],
                          "adapter_digest": given["adapter_digest"]},
            # THE ALLOCATION'S OWN ANSWER, unflattened, for the same reason.
            assignment_roots=roots, posture="execution",
            # THE ASSIGNMENT'S DECLARED OUTPUTS, forwarded. W39358: this
            # factory ACCEPTED `declared` and dropped it, so the adapter
            # had no declarations at all and the freeze refused every real
            # completed result with "the worker's envelope answers
            # 'proposal', which this assignment did not declare". The
            # worker answered exactly what the manager asked for; the
            # launcher never told the adapter what that was.
            outputs=declared,
            # AND THE MANIFEST THE RESULT IS SEALED AGAINST, dropped by
            # this factory for the same reason: it was accepted and never
            # forwarded, so the sealed result carried no input manifest
            # digest and broke the frozen schema.
            input_manifest_digest=input_manifest_digest,
                # THE WORKER'S OWN FIXED PATHS. `baton_worker` reads `/input` and
                # writes declared outputs under `/output`; a workspace bound
                # anywhere else is a workspace the agent cannot reach.
                mounts=[{"source": roots["inputs"], "target": "/input",
                         "writable": False},
                        {"source": roots["workspace"], "target": "/output",
                         "writable": True}],
                workspace_group=group,
                launch_delivery=launch,
                credential_delivery=credential_delivery,
                network=network,
                # INTERACTIVE, so idle PID 1 outlives the exec'd worker program
                # and the transport has something to `exec` into.
                interactive=True)

        return {"session": session, "bearer": _minted_bearer(),
                "credential_delivery": delivery,
                # WHAT THIS BUILDER OPENED, so the caller can close it. Review
                # 2026-08-30T18:34:00Z [P1]: the retry path was corrected and this
                # one was not, so the ORDINARY command left an authority and a
                # control store behind on every run -- and a handle this process
                # still holds is a lock the next incarnation waits on. One rule,
                # both builders.
                "closing": (store.close, authority.dispose),
                "open_store": lambda _place: store,
                "adapter_of": adapter_of, "run": _engine_run,
                "open_channel": lambda argv, *, seconds: _Channel(
                    argv, seconds=seconds)}



    except BaseException:                                # noqa: BLE001
        _unwinding(opened)
        raise

if __name__ == "__main__":
    # THE DOCUMENTED COMMAND, and it runs.
    #
    # The credential material is named by PATH on the command line and read
    # once into memory. It is not a grants member and not an environment
    # variable, because both are durable surfaces and §13 keeps the one
    # deliberate secret off every one of them; the path is not the secret.
    # Live provider authorization remains W39364's operator gate -- what this
    # does is hand whatever the operator authorized to the manager's own
    # credential home, which registers it live before a byte of it lands.
    import sys as _sys

    _credential = None
    for _index, _value in enumerate(_sys.argv):
        if _value == "--credential-file" and _index + 1 < len(_sys.argv):
            _credential = _sys.argv[_index + 1]

    def _provider(provider, reference):
        # TWO OPERANDS, because `CredentialHome.materialize` asks a provider
        # for a REFERENCE it resolved from the trusted profile. Found by the
        # positive launcher case; the one-operand version could never have
        # delivered a credential.
        del provider, reference
        if _credential is None:
            raise OperatorRefusal(
                "this attempt delivers a credential and no --credential-file "
                "was named; a provider secret is granted explicitly or not at "
                "all")
        # TEXT, because a materialized credential is durable text and the
        # manager holds it to that. Read whole and stripped of the trailing
        # newline an operator's editor adds, which is not part of the secret.
        with open(_credential, "r", encoding="utf-8") as _reading:
            return _reading.read().strip()

    _sys.exit(main(_sys.argv[1:],
                   capabilities=lambda given: _launched(
                       given, credential_provider=_provider),
                   retry_capabilities=_for_retry))
