"""THE INSTALLED ROLE CAPABILITY, and the pure predicate that matches it.

W376723, the first bounded slice of W371295 under owner E371253. The approved
shape is `PROPOSAL.md` SHA-256
`ad0f2171f06f8da9e6e3c2784e50cab91d27f94c4d0727014e4520b00aa0b339`, whose
`CAPABILITY.synthetic.json` canonicalizes to
`sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458c7bd8f649601`.

WHAT THIS IS. One closed document saying "this exact adapter, image and
runtime profile was qualified for these roles against that exact role
contract", and one PURE function that answers whether a capability and a
contract are compatible.

WHAT IT IS NOT, and the boundaries are the point:

  * NOT A QUALIFICATION GRANT. `qualification_digest` is required, bounded
    text and NOTHING here verifies what it refers to. The proposal is explicit
    that it names independently reviewed conformance evidence resolved by
    trusted installation tooling, and that "a self-authored worker
    advertisement grants nothing". This module checks SHAPE and AGREEMENT; it
    does not confer trust on either.
  * NOT A CARRIER. No deployment `/3`, derivation `/1` or resolution `/2`
    document is composed or read here, and no store, filesystem, engine or
    provider is touched. Those are the next slices.
  * NOT A DISPATCH DECISION. The predicate answers compatibility. Reservation,
    authorization, binding and servability remain with their existing owners,
    and this cannot certify any of them.
"""

import json
import re

from ..contracts import (ContractRefusal, canonical_bytes, digest,
                         digest_of_bytes, job_input_identity, own,
                         validate_fragment)
from ..contracts.errors import name_value
from .. import source_profiles, verification_context
from ..worker_manager import boundaries
from . import role_contract

__all__ = ["CAPABILITY_SCHEMA", "CAPABILITY_MEMBERS", "CAPABILITY_DIGESTS",
           "ROLE_SETS", "MAX_CAPABILITY_BYTES", "CANDIDATE_MEMBERS",
           "TUPLE_MEMBERS", "MANIFEST_TUPLE", "TASK_MEDIA_TYPE",
           "TASK_ARTIFACT", "MAX_TASK_BYTES", "TASK_SCHEMA",
           "TASK_MEMBERS", "TASK_SOURCE_ROOT", "check_dogfood_task",
           "capability_digest",
           "check_role_capability", "role_capability_of_bytes",
           "compatible_capability", "admissible_roles"]

CAPABILITY_SCHEMA = "baton.v12.adapter-role-capability/1"
# Closed, and in the order the proposal names them.
CAPABILITY_DIGESTS = ("role_contract_digest", "adapter_digest", "image_digest",
                      "runtime_profile_digest", "qualification_digest")
CAPABILITY_MEMBERS = ("schema",) + CAPABILITY_DIGESTS + ("roles",)

# THE THREE ADMITTED ROLE SETS, exactly: "No empty list, duplicates, wildcard
# identity or additional field." Spelled as the closed vocabulary rather than
# derived from a membership test, because "a non-empty subset of the contract's
# roles" would also admit an order this contract does not name.
ROLE_SETS = (["implementation"], ["review"], ["implementation", "review"])

# The proposal's own bounds. The DEPTH bound of 3 is checked by descent rather
# than restated as a number: this document is two levels deep by construction
# and `own` already refuses anything past the frozen limit.
MAX_CAPABILITY_BYTES = 2048

_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")


def _refuse(message):
    raise ContractRefusal("integrity", "schema", message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def capability_digest(document):
    """The canonical identity of one capability, over the WHOLE object.

    The same rule `role_contract.contract_digest` is under, for the same
    reason: no embedded digest member, so the identity is a fact about the
    bytes rather than a field the document asserts about itself.
    """
    return digest(own(document, what="an adapter role capability"))


def check_role_capability(document, *, what="an adapter role capability"):
    """The closed validator. Answers the owned document or refuses.

    PURE: no store, no filesystem, no configuration, no engine or provider,
    and no import of provider code. `own` comes first because every comparison
    below depends on the value space -- it takes a fresh snapshot, refuses
    floats and non-built-in objects, and keeps booleans and integers from
    becoming each other.
    """
    taken = own(document, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one closed object; this is "
                f"{name_value(document)}")
    missing = [one for one in CAPABILITY_MEMBERS if one not in taken]
    extra = sorted(one for one in taken if one not in CAPABILITY_MEMBERS)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(CAPABILITY_MEMBERS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    # THE SCHEMA IS ASKED FIRST. A capability from another revision is not one
    # to read the recognised parts out of.
    if taken["schema"] != CAPABILITY_SCHEMA:
        _denied(f"{what} says it is {name_value(taken['schema'])} and this "
                f"build reads exactly {name_value(CAPABILITY_SCHEMA)}")
    for name in CAPABILITY_DIGESTS:
        value = taken[name]
        # LOWER-CASE HEX WITH THE PREFIX, and a WILDCARD IS NOT AN IDENTITY.
        # The proposal forbids one by name; what makes that enforceable is
        # that nothing but this exact spelling is admitted at all.
        if type(value) is not str or not _DIGEST.match(value):
            _refuse(f"{what}'s {name} is {name_value(value)}; an installed "
                    f"capability names each identity as one lower-case "
                    f"sha256 digest, and there is no wildcard spelling",
                    )
    roles = taken["roles"]
    if type(roles) is not list or roles not in [list(one)
                                                for one in ROLE_SETS]:
        _refuse(f"{what} declares roles {json.dumps(roles)[:120]}; an "
                f"installed capability declares exactly one of "
                f"{json.dumps([list(one) for one in ROLE_SETS])} -- no empty "
                f"list, no duplicate and no other order")
    if len(canonical_bytes(taken)) > MAX_CAPABILITY_BYTES:
        _refuse(f"{what} is wider than {MAX_CAPABILITY_BYTES} canonical "
                f"bytes")
    return taken


def role_capability_of_bytes(payload, *, what="an adapter role capability"):
    """One capability read from BYTES, bounded, with duplicate keys refused.

    DUPLICATE KEYS REFUSE BEFORE CANONICALIZATION, which is the same subtle
    fault `role_contract.role_contract_of_bytes` closes: `json.loads` keeps
    the LAST of two equal keys silently, so a document carrying `roles` twice
    has two readings -- the one a reader sees and the one a digest is taken
    over. Two parties could then agree on a digest and disagree on the grant.
    """
    if type(payload) is not bytes:
        _refuse(f"{what} is read from bytes; this is {name_value(payload)}")
    if len(payload) > MAX_CAPABILITY_BYTES:
        _refuse(f"{what} is {len(payload)} encoded bytes and this contract "
                f"admits {MAX_CAPABILITY_BYTES}")

    def _pairs(pairs):
        seen = {}
        for name, value in pairs:
            if name in seen:
                _refuse(f"{what} carries the member {name_value(name)} "
                        f"twice; a document with two readings has no "
                        f"identity")
            seen[name] = value
        return seen

    try:
        document = json.loads(payload.decode("utf-8"),
                              object_pairs_hook=_pairs)
    except UnicodeDecodeError:
        _refuse(f"{what} is UTF-8 text")
    except ValueError:
        _refuse(f"{what} is one readable JSON document")
    return check_role_capability(document, what=what)


def compatible_capability(capability, contract, *, what="this deployment"):
    """THE PURE PREDICATE. Answers the agreed roles, or refuses with the
    exact disagreement.

    WHAT AGREEMENT MEANS HERE, and it is narrow on purpose:

      * the capability is a valid `capability/1` and the contract is a valid
        `development-role-contract/1` -- both through their own owners, so
        neither is trusted as already-checked data;
      * the capability's `role_contract_digest` IS the contract's canonical
        digest, computed rather than compared to a claim the document carries
        about itself;
      * and every role the capability declares is a role the contract
        declares, so a capability cannot grant a role the workflow has no
        stage for.

    WHAT IT DOES NOT MEAN. Nothing here says the adapter behind those digests
    behaves as the contract declares -- that is the qualification evidence
    `qualification_digest` refers to and W371296's actual adapter
    qualification. And nothing here reserves, authorizes, binds or admits:
    this is a predicate, and the existing owners still decide.
    """
    held = check_role_capability(capability)
    agreed = role_contract.check_role_contract(contract)
    mine = role_contract.contract_digest(agreed)
    if held["role_contract_digest"] != mine:
        _denied(f"{what}'s installed capability was qualified against role "
                f"contract {name_value(held['role_contract_digest'])} and "
                f"this Job resolves {name_value(mine)}; a capability proves "
                f"nothing about a contract it was not qualified against")
    declared = [one["role"] for one in agreed["roles"]]
    unknown = [one for one in held["roles"] if one not in declared]
    if unknown:
        _denied(f"{what}'s installed capability declares the role(s) "
                f"{', '.join(unknown)} and this contract declares "
                f"{', '.join(declared)}; a capability cannot grant a role "
                f"this workflow has no stage for")
    return list(held["roles"])


# WHAT THIS MODULE IS HELD TO AT IMPORT.
#
# The approved synthetic vector's canonical digest, from PROPOSAL.md. It is
# SYNTHETIC -- its four repeated-digit hashes are explicitly not qualified
# deployments or owner receipts -- so what this pins is the SHAPE and the
# canonical form, never a grant.
SYNTHETIC_DIGEST = (
    "sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458c7bd8f649601")
_SYNTHETIC = {
    "schema": CAPABILITY_SCHEMA,
    "role_contract_digest": role_contract.BASELINE_DIGEST,
    "adapter_digest": "sha256:" + "1" * 64,
    "image_digest": "sha256:" + "2" * 64,
    "runtime_profile_digest": "sha256:" + "3" * 64,
    "qualification_digest": "sha256:" + "4" * 64,
    "roles": ["implementation", "review"],
}
assert capability_digest(_SYNTHETIC) == SYNTHETIC_DIGEST, \
    capability_digest(_SYNTHETIC)
# It validates, and it is compatible with the accepted baseline contract --
# which is what makes the positive side of the predicate a reproduced fact
# rather than a fixture of mine.
assert check_role_capability(_SYNTHETIC) == _SYNTHETIC
assert compatible_capability(
    _SYNTHETIC, role_contract.baseline_document()) == [
        "implementation", "review"]
# And `boundaries` is imported for the refusal vocabulary this package shares;
# naming it keeps the dependency visible rather than implicit.
assert boundaries is not None


# -- the pure owned-data admission boundary ----------------------------------
#
# W376723 reviews 2026-10-28T20-04-10Z and 2026-10-28T20-08-41Z. The first
# found that `compatible_capability` took only a capability and a contract, so
# the tuple binding, the final per-role declarations, the task and source
# agreement, role eligibility and principal separation -- all of which the
# FINDING assigns here -- did not exist. The second reproduced three
# counterexamples in the first attempt at this boundary and named a fourth
# structural fault. All four are closed below and each one is marked.
#
# PURE AND OWNED-DATA ONLY. No store, filesystem, engine, provider, callback or
# import of provider code; every operand is data a caller already composed, and
# each one is owned THROUGH ITS OWN OWNER rather than by a second validator
# here: the capability through `check_role_capability`, the contract through
# `check_role_contract`, and the actual composed input through
# `contracts.validate_fragment` and `contracts.job_input_identity`.

CANDIDATE_MEMBERS = ("worker_id", "principal", "capability", "installed",
                     "task_document", "input_manifest")

# W376723 review 2026-10-28T21-35-39Z: `task_schema` and `source_profile` were
# LABELS, and a matching label is not validation of the underlying composed
# input -- the same distinction this boundary already learned for the invented
# `job_projection`. `TASK-BOUNDARY.json` reproduces it: the baseline was
# admitted while its manifest's human contract was `text/markdown`, which the
# installed task delivery refuses. So the operand is now the ACTUAL composed
# task document and both labels are DERIVED from it.
#
# THE MEDIA TYPE IS A SECOND COPY ON PURPOSE. `tools/job_task.py` owns the
# delivery and `src/` may not import `tools/` -- that layering is the reason
# the constant is spelled here rather than imported, and
# `test_role_capability` holds the two against each other exactly as
# `test_exchange` holds the worker's and the manager's copies of the exchange
# vocabulary. Two copies of one contract agree until they don't.
TASK_MEDIA_TYPE = "application/json"

# What a composed task artifact must say about the bytes, closed: the three
# members `job_task.manifest_for` replaces, which are the three that describe
# them.
TASK_ARTIFACT = ("media_type", "bytes", "content_digest")

# The task document's own ceiling. `single_worker.MAX_TASK_BYTES` bounds the
# delivered document and this reader is handed one a caller already composed,
# so it bounds what it will decode rather than trusting the composer.
MAX_TASK_BYTES = 1 << 20

# -- the supported `/2` task contract ----------------------------------------
#
# W376723 review 2026-10-28T22-37-51Z. `verification_context.generation`
# answers WHICH GENERATION a task declares -- the version, and whether it
# carries the `/3` context member. It does not establish the supported shape,
# and the review's probe is the proof: four fully digest-bound pairs were
# ADMITTED here and REFUSED by the consuming reader, `claude_agent._read_task`
# -- a task carrying only a schema and a profile, a `verification` that is a
# string, an unknown member, and a numeric `task_id`. `job_task.compose_task`
# cannot catch them either: it substitutes two members and says explicitly
# that it does not validate the vocabulary.
#
# SO THE SUPPORTED SHAPE IS ESTABLISHED HERE, and it agrees with the consumer
# by MEASUREMENT rather than by assertion: `TheTwoTaskReadersAgree` drives
# both this validator and the real worker reader over one vector set and
# requires the same answer from each.
#
# WHY THE VOCABULARY IS SPELLED HERE RATHER THAN IMPORTED. The consumer is a
# PROVIDER ADAPTER inside the worker image, and the review is explicit that it
# must not be imported into the generic host -- that is the isolation the
# images are built on. `claude_agent.py` is also W376586's current candidate
# and under review, so extracting a shared module in this claim would be an
# uncoordinated edit to another open slice. PROGRESS records the single owning
# home as the coordinated follow-up; what is NOT deferred is the agreement,
# which is proved now.
#
# AND THE PROFILE RULES ARE NOT RESPELLED. `baton_v12.source_profiles` is the
# owner of the profile vocabulary and of the declared-base pairing, it lives
# in this package, and the worker's own reader defers to it for exactly these
# two members -- "the pairing is the profile package's rule, not a second copy
# of it". This defers to the same owner.
TASK_SCHEMA = "baton.dogfood-task/2"
TASK_MEMBERS = ("schema", "task_id", "instructions", "verification",
                "source_root", "source_profile", "declared_base")
# The one staged source root. HELD BY EQUALITY, because the consuming workload
# stages exactly this path: "the source is a constant of the contract rather
# than a value the task selects".
TASK_SOURCE_ROOT = "source"
_TASK_ID = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}\Z")

# WHERE THE PAIRING RULE IS ASKED FROM, and these are the CONSUMING CONTRACT'S
# OWN FIXED PATHS rather than anything this boundary chooses. `checkout_plan`
# takes a mounted source and a workspace because it composes a PLAN; this
# boundary discards the plan and keeps only the refusal, so the two operands
# exist to satisfy the rule's signature and nothing here decides a workspace.
# `test_verification_context` asks the same rule the same way with the same two
# paths, which is the established idiom: "this module ASKS that package through
# an injected operand rather than restating it. A second copy of the pairing is
# a second rule."
_PAIRING_SOURCE = "/input/source"
_PAIRING_WORKSPACE = "/output"


def _paired(profile, declared, where):
    """The profile/base pairing, THROUGH THE PACKAGE THAT DEFINES IT.

    W376723 review 2026-10-28T23-13-01Z. `check_dogfood_task` held the profile
    to the vocabulary and the base to its shape, which is what the consuming
    reader does -- and the consuming reader can afford to, because it defers
    the PAIRING to `checkout_plan` later in the same turn. A pre-effect
    admission predicate cannot: `git-line` with a null `declared_base` was
    ADMITTED for both roles here while `checkout_plan` refuses it, so a lane
    nobody could check out passed the boundary whose whole job is to refuse
    before effects.

    THE RULE IS NOT RESTATED. `checkout_plan` refuses a version-control
    profile with no base AND a generic profile WITH one, both halves, and it is
    asked here rather than copied -- a second copy of the pairing is a second
    rule, and this one would drift the moment a third profile arrived.
    """
    try:
        source_profiles.checkout_plan(_PAIRING_SOURCE, _PAIRING_WORKSPACE,
                                      profile=profile, declared=declared)
    except source_profiles.ProfileRefusal as refusal:
        _denied(f"{where}'s task pairs source_profile "
                f"{name_value(profile)} with declared_base "
                f"{name_value(declared)}, which the profile package refuses: "
                f"{refusal}")


def check_dogfood_task(document, *, what="a composed task"):
    """The supported `/2` task document, closed, or a refusal.

    PURE OWNED DATA. No filesystem, no callback, no provider import: every
    rule below is a comparison over the caller's own built-in data, and the
    two members with an existing owner are handed to that owner.

    THE ORDER IS THE CONSUMER'S, so the two readers refuse the same input for
    the same reason: the member set, then the schema, then the identity, then
    the text members, then the staged root by equality, then the verification
    words, then the profile and its base.
    """
    taken = own(document, what=what)
    if type(taken) is not dict:
        _refuse(f"{what} is one JSON object; this is {name_value(document)}")
    missing = sorted(one for one in TASK_MEMBERS if one not in taken)
    extra = sorted(one for one in taken if one not in TASK_MEMBERS)
    if missing or extra:
        _refuse(f"{what} is exactly {', '.join(TASK_MEMBERS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    if taken["schema"] != TASK_SCHEMA:
        _denied(f"{what} says it is {name_value(taken['schema'])} and this "
                f"contract supports {name_value(TASK_SCHEMA)}; a task from "
                f"another generation is not one to read the recognised parts "
                f"out of")
    # TEXT BEFORE IT IS MATCHED, which is W44424's correction at the consumer:
    # a JSON number reached the regex as its decimal spelling and passed, so
    # the identity of a versioned document was decided by a coercion.
    if type(taken["task_id"]) is not str \
            or not _TASK_ID.match(taken["task_id"]):
        _refuse(f"{what} carries no usable task identity; this is "
                f"{name_value(taken['task_id'])}")
    for name in ("instructions", "source_root"):
        if type(taken[name]) is not str or not taken[name]:
            _refuse(f"{what} carries a {name} that is not bounded non-empty "
                    f"text; this is {name_value(taken[name])}")
    if taken["source_root"] != TASK_SOURCE_ROOT:
        _denied(f"{what} names source_root {name_value(taken['source_root'])} "
                f"and the workload stages exactly "
                f"{name_value(TASK_SOURCE_ROOT)}")
    verification = taken["verification"]
    if type(verification) is not list or not verification \
            or not all(type(one) is str and one for one in verification):
        _refuse(f"{what} carries a verification that is a non-empty list of "
                f"words; a command assembled from a string is a shell, and "
                f"there is no shell here")
    # THE PROFILE AND ITS BASE, THROUGH THEIR OWN OWNER.
    if taken["source_profile"] not in source_profiles.PROFILES:
        _denied(f"{what} names source_profile "
                f"{name_value(taken['source_profile'])} and the workload "
                f"consumes {' and '.join(source_profiles.PROFILES)}")
    if taken["declared_base"] is not None:
        try:
            source_profiles.check_declared_base(taken["declared_base"])
        except source_profiles.ProfileRefusal as refusal:
            _denied(f"{what} carries a declared_base the workload cannot "
                    f"use: {refusal}")
    # AND THE PAIRING, which the consuming reader defers and a PRE-EFFECT
    # predicate may not. See `_paired`.
    _paired(taken["source_profile"], taken["declared_base"], what)
    return taken
TUPLE_MEMBERS = ("adapter_digest", "image_digest", "runtime_profile_digest")

# WHICH TUPLE MEMBERS THE ACTUAL COMPOSED INPUT ALSO CARRIES, and under which
# names. The input manifest states the image and the runtime profile this lane
# will really run, so the resolved tuple is held against the lane's own
# composed input rather than only against its capability -- an `installed`
# tuple nothing else mentions is an assertion, not a binding. The adapter
# digest has no manifest member, which is exactly why `qualification_digest`
# and W371296 exist.
MANIFEST_TUPLE = {"image_digest": "worker_image_digest",
                  "runtime_profile_digest": "runtime_profile_digest"}

# How much of an owner's refusal travels in a lane-labelled refusal. Bounded
# because the message is composed from a document this boundary did not author.
MAX_CARRIED_REASON = 240


def _identical(mine, theirs):
    """Type-sensitive structural equality.

    REVIEW COUNTEREXAMPLE 1, and it was exactly right: a candidate declaring
    `required: 0` was accepted against a descriptor declaring `required: false`,
    because Python's `==` holds `0 == False` and `1 == True`. `own` preserves
    built-in types -- it does not make ordinary equality type-sensitive -- so
    comparing two owned documents with `==` compares the WRONG RELATION. A
    Boolean that arrives as an integer is a different declaration, and the one
    place that matters most is `required`, which decides whether a stage may
    succeed without an output.

    `type(...) is type(...)` rather than `isinstance`, so `bool` and `int` are
    distinct here as they are in the frozen descriptor.
    """
    if type(mine) is not type(theirs):
        return False
    if type(mine) is dict:
        return sorted(mine) == sorted(theirs) and all(
            _identical(mine[name], theirs[name]) for name in mine)
    if type(mine) is list:
        return len(mine) == len(theirs) and all(
            _identical(one, other) for one, other in zip(mine, theirs))
    return mine == theirs


def _disagreement(mine, theirs, where="value"):
    """The FIRST type-sensitive disagreement, named by its path.

    A refusal that says only "these differ" sends a reader to diff two
    documents by eye; this names the member and both types, which is the
    difference between a message and an answer.
    """
    if type(mine) is not type(theirs):
        return (f"{where} is {type(mine).__name__} "
                f"{name_value(mine)} and this contract fixes "
                f"{type(theirs).__name__} {name_value(theirs)}")
    if type(mine) is dict:
        extra = sorted(one for one in mine if one not in theirs)
        missing = sorted(one for one in theirs if one not in mine)
        if extra or missing:
            return (f"{where} is exactly {', '.join(sorted(theirs))}"
                    + (f"; missing {', '.join(missing)}" if missing else "")
                    + (f"; unexpected {', '.join(extra)}" if extra else ""))
        for name in sorted(mine):
            if not _identical(mine[name], theirs[name]):
                return _disagreement(mine[name], theirs[name],
                                     f"{where}.{name}")
        return None
    if type(mine) is list:
        if len(mine) != len(theirs):
            return (f"{where} holds {len(mine)} entries and this contract "
                    f"fixes {len(theirs)}")
        for index, (one, other) in enumerate(zip(mine, theirs)):
            if not _identical(one, other):
                return _disagreement(one, other, f"{where}[{index}]")
        return None
    if mine != theirs:
        return (f"{where} is {name_value(mine)} and this contract fixes "
                f"{name_value(theirs)}")
    return None


def _exact(mine, theirs, where, what):
    """One value held to the contract's, type-sensitively, or a denial."""
    if not _identical(mine, theirs):
        _denied(f"{what}: {_disagreement(mine, theirs, where)}")
    return mine


def _composed_task(value, manifest, contract, where):
    """The lane's ACTUAL composed task, validated and bound to its manifest.

    W376723 review 2026-10-28T21-35-39Z. Three facts, and none of them is a
    label a caller asserted:

      * THE SUPPORTED TASK GENERATION, answered by `verification_context.
        generation` -- the existing data-only owner of that question, which
        refuses anything outside its two generations and refuses a `/2`
        carrying a `/3` member or a `/3` without one. The contract then fixes
        WHICH generation this template supports, so an otherwise valid `/3`
        task under a `/2` contract refuses here rather than at a worker.
      * THE SOURCE PROFILE, read out of the TASK and held to the contract's.
      * THE EXACT ARTIFACT BINDING. The manifest's human contract is this
        profile's task delivery, so its media type, byte count and content
        digest must describe THESE bytes -- which is what makes the manifest's
        Job input identity a statement about this task rather than about a
        document nobody has.

    ANSWERS THE TASK'S DIGEST, so the lanes can be held to one common task.

    ONE ENCODING, which is `job_task.delivered_bytes`'s rule restated for the
    same reason it exists there: "the bytes the artifact names" and "the bytes
    the worker reads" must not be two renderings of one string.
    """
    if type(value) is not str or not value:
        _refuse(f"{where} composes its task as the one text its delivery "
                f"encodes; this is {name_value(value)}")
    raw = value.encode("utf-8")
    if len(raw) > MAX_TASK_BYTES:
        _refuse(f"{where}'s composed task is {len(raw)} encoded bytes and "
                f"this boundary reads {MAX_TASK_BYTES}")
    try:
        task = json.loads(raw.decode("utf-8"))
    except ValueError:
        _refuse(f"{where}'s composed task is one readable JSON document")
    if type(task) is not dict:
        _refuse(f"{where}'s composed task is one object; this is "
                f"{name_value(task)}")
    # THE GENERATION THROUGH ITS OWN OWNER, which answers WHICH generation
    # this document declares and whether it carries the `/3` context member.
    try:
        generation = verification_context.generation(task)
    except verification_context.ContextRefusal as refused:
        _denied(f"{where}'s composed task is not one this build's task owner "
                f"reads ({refused})")
    _exact(generation, contract["task_schema"], "its task generation",
           f"{where} composes an unsupported task")
    # AND THEN THE SUPPORTED SHAPE, which the generation does not establish.
    # Review 2026-10-28T22-37-51Z: four fully digest-bound pairs passed this
    # boundary and were refused by the consuming reader, because a generation
    # label plus a correct artifact digest is not a task contract.
    checked = check_dogfood_task(task, what=f"{where}'s composed task")
    _exact(checked["source_profile"], contract["source_profile"],
           "its task's source profile",
           f"{where} composes an unsupported source")
    # AND THE ARTIFACT THE MANIFEST DELIVERS IT AS, member for member.
    contracted = manifest.get("human_contract")
    if type(contracted) is not dict:
        _denied(f"{where}'s composed input carries no human contract artifact, "
                f"so there is no task delivery for its task to be")
    wanted = {"media_type": TASK_MEDIA_TYPE, "bytes": len(raw),
              "content_digest": digest_of_bytes(raw)}
    for name in TASK_ARTIFACT:
        if not _identical(contracted.get(name), wanted[name]):
            _denied(f"{where}'s task delivery declares {name} "
                    f"{name_value(contracted.get(name))} and its composed task "
                    f"is {name_value(wanted[name])}; an artifact that does not "
                    f"describe these bytes delivers a document nobody has")
    return wanted["content_digest"]


def _composed_input(value, where):
    """The lane's ACTUAL composed input, owned through ITS OWN OWNER.

    REVIEW COUNTEREXAMPLE 3. The first attempt took a `job_projection` operand
    and compared the two lanes' values with equality, so two lanes passing
    `None` -- or any two equal labels a caller invented -- were accepted as a
    common Job projection. "Equality of arbitrary caller labels is not
    establishment of supported common Job-scoped input facts."

    So the operand is the lane's real input manifest and the projection is
    DERIVED from it by `contracts.job_input_identity`, which is the rule that
    already owns this question: it validates the document against the frozen
    `inputManifest` definition, verifies its self-digest, refuses a durable
    secret, and projects out exactly the per-execution members --
    `worker_image_digest`, `toolchain_digest`, `runtime_profile_digest`,
    `credential_policy_digest`, `role_instructions_digest`, `manifest_id`,
    `created_at` and the digest itself. An absent or invalid manifest cannot
    reach agreement, and two lanes on two images still share one identity,
    which is the `ID-4` distinction this slice exists to keep.

    NOTHING IS READ FROM DISK. The frozen contract is bytes the `contracts`
    package already holds; this is computation over the caller's own data.
    """
    owned = validate_fragment(value, "inputManifest", what=where)
    # THE IDENTITY IS TAKEN FROM THE OWNED COPY, so the document a caller can
    # still mutate is not the one this answer was derived from.
    return owned, job_input_identity(owned, what=where)


def _admissible_lane(role, candidate, contract, *, what):
    """ONE lane's admission facts, from ITS OWN capability and ITS OWN tuple.

    NAMED `_admissible_lane` RATHER THAN `_lane`, and that is not style.
    `job_manager/scheduler.py` already defines a private `_lane`, and
    `test_boundary_inventory` resolves private helper returns by BARE FUNCTION
    NAME across the whole package with the first module in sorted order
    winning -- so a second `_lane` here would silently retarget that registry
    entry, which is the drift `exchange._vocabulary` records having caused.

    THE STRUCTURAL FAULT REVIEW 20-08-41Z NAMED. The first attempt took ONE
    capability and ONE installed tuple for every candidate, so it could not
    establish independent image/adapter/profile binding for heterogeneous
    lanes -- and the case that claimed to prove heterogeneity varied only
    `worker_id`. Each lane now carries its own trusted capability and its own
    resolved tuple, and this helper checks the binding between them and the
    lane's actual composed input.

    A SINGLE-ROLE CAPABILITY IS A VALID LANE INPUT, which the review is
    explicit about: what it cannot do is stand for the whole stage decision.
    That part is `admissible_roles`', below.
    """
    where = f"{what}'s {role} candidate"
    # `type(...) is dict` rather than `own`: the candidate holds whole
    # documents, each of which is owned by its own owner below, and a blanket
    # deep snapshot here would both duplicate that and run the nested manifest
    # past the frozen depth bound. What this needs from `own` is the one
    # property it cannot get later -- that the mapping is a real `dict` and not
    # a subclass executing its own `__getitem__` inside this boundary.
    if type(candidate) is not dict:
        _refuse(f"{where} is one closed object; this is "
                f"{name_value(candidate)}")
    missing = [one for one in CANDIDATE_MEMBERS if one not in candidate]
    extra = sorted(one for one in candidate if one not in CANDIDATE_MEMBERS)
    if missing or extra:
        _refuse(f"{where} is exactly {', '.join(CANDIDATE_MEMBERS)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    boundaries.text(candidate["worker_id"], f"{where}'s worker id")
    boundaries.text(candidate["principal"], f"{where}'s principal")
    # THIS LANE'S OWN TRUSTED CAPABILITY, OWNED ONCE, against the ALREADY-OWNED
    # contract -- never the caller's original of either. The owned copy below
    # is what the tuple is compared against, so the document a caller can still
    # mutate is not the one this decision reads.
    checked = check_role_capability(candidate["capability"], what=where)
    covered = compatible_capability(checked, contract, what=where)
    if role not in covered:
        _denied(f"{where}'s capability is qualified for "
                f"{', '.join(covered)} and this lane serves "
                f"{name_value(role)}; a capability for another role is not "
                f"evidence about this one")
    held = own(candidate["installed"], what=f"{where}'s installed tuple")
    if type(held) is not dict or sorted(held) != sorted(TUPLE_MEMBERS):
        _refuse(f"{where}'s installed tuple is exactly "
                f"{', '.join(TUPLE_MEMBERS)}; this is {name_value(held)}")
    for name in TUPLE_MEMBERS:
        if type(held[name]) is not str or not _DIGEST.match(held[name]):
            _refuse(f"{where}'s installed {name} is {name_value(held[name])}; "
                    f"a resolved runtime identity is one lower-case sha256 "
                    f"digest")
        if held[name] != checked[name]:
            _denied(f"{where} resolved {name} {name_value(held[name])} and "
                    f"its capability was qualified for "
                    f"{name_value(checked[name])}; a capability is evidence "
                    f"about one tuple and proves nothing about another")
    # AND THE TUPLE IS BOUND TO THE ACTUAL COMPOSED INPUT, not only to the
    # capability. A resolved identity no composed input mentions is a claim
    # about a runtime nobody is going to start.
    try:
        owned, identity = _composed_input(candidate["input_manifest"],
                                          f"{where}'s composed input")
    except ContractRefusal as refusal:
        _denied(f"{where}'s composed input manifest is not one this Job can "
                f"admit: {str(refusal)[:MAX_CARRIED_REASON]}")
    for name, member in sorted(MANIFEST_TUPLE.items()):
        if owned.get(member) != held[name]:
            _denied(f"{where} resolved {name} {name_value(held[name])} and "
                    f"its composed input declares {member} "
                    f"{name_value(owned.get(member))}; the admitted tuple is "
                    f"the one the lane will actually run")
    # THE FINAL DECLARATIONS, FROM THE ACTUAL COMPOSED INPUT, member for
    # member and in order, type-sensitively. This is where an incompatibility
    # used to reach a running adapter -- and the declarations compared are the
    # manifest's own, so a caller cannot pass a tidy list beside a manifest
    # that says something else.
    _exact(owned["outputs"], contract["outputs"], "its declared outputs",
           f"{where} declares a different result contract")
    # THE ACTUAL TASK, AND ITS BINDING TO THIS LANE'S OWN COMPOSED INPUT.
    # Asked after the manifest is owned, because the binding is a fact about
    # the owned artifact rather than about the document a caller passed.
    task = _composed_task(candidate["task_document"], owned, contract, where)
    return {"worker_id": candidate["worker_id"],
            "principal": candidate["principal"],
            "job_input_identity": identity, "task_digest": task}


def admissible_roles(contract, *, candidates, what="this deployment"):
    """The roles this deployment may serve, ALL of them, or the exact refusal.

    `contract` is the development role contract this Job resolves, and it is
    owned ONCE here: review 20-08-41Z noted that the first attempt validated a
    copy and then reread the caller's original for outputs, task and source,
    which is a validated-looking alias rather than a validated document.

    `candidates` maps EVERY role the contract declares to that lane's final
    composed inputs -- its own trusted capability, its own resolved
    adapter/image/runtime-profile tuple, its worker id and principal, its task
    and source, and its actual input manifest.

    WHAT IT ANSWERS: the contract's declared roles, as a fresh detached list,
    when every one of them has an independently eligible lane. It is a
    PREDICATE: nothing here reserves, authorizes, binds, dispatches or admits,
    and no qualification is minted -- `qualification_digest` is still only
    required text that nothing in this module verifies.

    REVIEW COUNTEREXAMPLE 2 is the reason the answer is the CONTRACT's roles
    rather than a capability's. The first attempt computed the missing roles
    from the capability, so a capability declaring `["implementation"]` with
    one matching candidate answered `["implementation"]` for a contract
    requiring implementation AND review -- a full admission for half a
    workflow. A single-role capability remains a valid LANE input; it cannot
    be the stage decision.
    """
    agreed = role_contract.check_role_contract(
        contract, what=f"{what}'s role contract")
    required = [one["role"] for one in agreed["roles"]]
    if type(candidates) is not dict:
        _refuse(f"{what}'s role candidates are one object keyed by role; this "
                f"is {name_value(candidates)}")
    missing = [one for one in required if one not in candidates]
    if missing:
        _denied(f"{what}'s contract requires {', '.join(required)} and no "
                f"candidate was composed for {', '.join(missing)}; a required "
                f"role with no independently eligible lane cannot be served, "
                f"and another role's capability does not supply one")
    extra = sorted(one for one in candidates if one not in required)
    if extra:
        _denied(f"{what} composed a candidate for {', '.join(extra)}, which "
                f"this contract does not declare")
    lanes = {role: _admissible_lane(role, candidates[role], agreed, what=what)
             for role in required}
    # ONE COMMON JOB-SCOPED INPUT IDENTITY, and per-lane runtime identities
    # left alone. Both halves are the point: the identity is DERIVED by the
    # rule that owns it, and the members it projects out are exactly the ones
    # a heterogeneous lane is allowed to differ in.
    identities = {one["job_input_identity"] for one in lanes.values()}
    if len(identities) > 1:
        _denied(f"{what}'s lanes compose different Job input identities "
                f"({', '.join(sorted(name_value(one) for one in identities))});"
                f" the Job-scoped facts are common even though each lane keeps "
                f"its own runtime identity")
    # ONE COMMON ACTUAL TASK. The FINDING and the proposal's "Binding and
    # heterogeneous execution" both require it, so it is asked directly rather
    # than left implied -- and it IS also implied, because the task artifact's
    # digest is inside the manifest the Job input identity is taken over, so
    # two lanes on two tasks already disagree above. Stated plainly: this is a
    # SECOND LINE over the same fact, kept because the two are owned by
    # different documents and a later revision could move one.
    tasks = {one["task_digest"] for one in lanes.values()}
    if len(tasks) > 1:
        _denied(f"{what}'s lanes compose different tasks "
                f"({', '.join(sorted(name_value(one) for one in tasks))}); one "
                f"Job is one task, and a lane reviewing another task's "
                f"candidate is reviewing something nobody asked for")
    # PRINCIPAL SEPARATION, and two worker ids do not create independence.
    principals = {}
    for role in required:
        principals.setdefault(lanes[role]["principal"], []).append(
            lanes[role]["worker_id"])
    shared = {who: ids for who, ids in principals.items() if len(ids) > 1}
    if shared:
        who, ids = sorted(shared.items())[0]
        _denied(f"{what} serves more than one role as {name_value(who)} "
                f"(workers {', '.join(sorted(ids))}); independent review is a "
                f"separation of principals, and two worker ids do not create "
                f"one")
    return list(required)
