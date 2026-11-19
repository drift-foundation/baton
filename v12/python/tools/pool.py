"""Admit ONE worker into an installed instance's pool. W202663.

WHAT THIS IS FOR. `tools.bootstrap` composes a deployment once, from one input
document, and every worker it configures is named there. An instance that is
already installed therefore has no way to GROW: re-running the bootstrap
against a new input is how a deployment is repeated, not how a pool is
extended, and a pool that can only be extended by hand-editing the emitted
`deployment.json` is one that will be extended by hand-editing it. This verb is
the small provable alternative -- one worker, admitted into the configuration an
instance already has, held to exactly the rules that worker would have been
held to had it been named at install.

WHAT IT DOES NOT DO, and none of these is an oversight:

  it prepares no Job, binds no Work and submits nothing;
  it creates and touches no Work, grant, route handler, capability or policy.
    The Authority is opened to RESOLVE A PRINCIPAL and for nothing else, and
    only when this root already has one -- see `principal_of`, which is a read;
  it removes and modifies no worker that is already configured. The entry it
    appends is the only difference between the file it read and the file it
    wrote, `pool_generation` aside -- see THE ONE OTHER MEMBER below;
  it activates no pool and opens no Job store for writing. The generation it
    prints is the one the SCHEDULER will mint at the next activation, read from
    the Job store through its non-writing opener rather than decided here.

THE RULES ARE BOOTSTRAP'S, CALLED RATHER THAN COPIED. A second, more permissive
idea of what a valid worker is would be worth less than nothing: it would admit
into a live instance documents the install path refuses, and the operator would
discover that at the next activation. So the worker's own shape is held to
`bootstrap._WORKER`, its identity to `bootstrap._safe_name`, its principal to
`bootstrap.principals_for`, and the whole amended configuration to
`bootstrap.validated` -- which is the accepted `stage_execution` validator, the
same call `bootstrap.prepare` makes. That is where the manifest comparison the
operator most needs lives: a worker whose `image_digest` is not its own input
manifest's `worker_image_digest` is refused by `single_worker._held`, by name,
before anything is written.

NOTHING DURABLE UNTIL EVERY CHECK HAS PASSED, which is `tools.bootstrap`'s own
order and for its own reason: a refusal that has already changed durable state
is not a refusal. The configuration is read, the worker is held, the amended
document is proved, the pool it composes is owned and the generation is read --
and only then is one file replaced, atomically, by bootstrap's own publisher.

THE ONE OTHER MEMBER. `pool_generation` moves to the value this prints, and it
is not a second edit: `stage_execution._pool_generation` refuses a deployment
whose configured generation is not the one activating its pool would answer, so
the generation is a DERIVED FACT ABOUT THE WORKERS rather than an independent
selection. Admitting a worker into a pool that has already been activated and
leaving the old number behind would write a configuration the manager refuses
to serve -- an instance broken by the command that was meant to grow it. On an
instance whose pool has never been activated the minted generation is 1, which
is what such a configuration already names, and the member does not move at all.

WHAT IT CANNOT DO FOR YOU, said here rather than discovered at the first claim.
A worker's participant is authorized for its stage's route by a route handler
on the Authority, and `bootstrap._compose` adds one for every worker it
configures. Adding one is a durable Authority act that bumps the policy
generation, so this verb does not: a worker admitted under a participant the
Authority does not already handle for its role's route is configured and will
have its claims refused. Admit under a participant this deployment already
serves, or add the handler yourself before the next activation. For the same
reason this derives no repository clone and no workspace storage under the
destination the way an installation does -- `nominated_source` and
`workspace_storage` are named by the document you supply, and are proved to be
real and outside the checkout by the accepted validator.
"""
import argparse
import json
import os
from pathlib import Path
import sys

from tools import bootstrap
from tools import single_worker
from tools import stage_execution

VERB = "add-worker"

# ONE REFUSAL TYPE, AND IT IS THE OWNER'S. Most of what this verb refuses is
# refused inside `tools.bootstrap` -- the manifest comparison, the profile
# shape, the principal resolution -- because those rules are called rather than
# copied. A second exception class here would make every caller of this module
# catch two exceptions for one answer, and would invite the next reader to
# suppose the two mean different things.
PoolRefusal = bootstrap.BootstrapRefusal

# WHERE THIS INSTANCE'S JOB STORE IS, derived from the Authority store the
# configuration already names rather than from a second operand nothing would
# keep equal to it. Both layouts this build writes -- `bootstrap.layout` for a
# state root and `instance.layout` for an installed destination -- put the four
# stores in ONE directory, so the Job store is the Authority store's sibling.
# The basename is taken from the layout rather than spelled again here.
JOB_STORE_NAME = os.path.basename(bootstrap.layout(os.sep)["job_store"])

# What a reader of a Job store calls itself. It is a READ-ONLY handle: it
# initializes nothing, migrates nothing and requests no journal mode, so this
# name reaches no row -- `JobStore.open_readonly` still requires one, for the
# reason every store does.
INCARNATION = "pool-add-worker"


# -- the two documents --------------------------------------------------------


def _read(place, limit, what):
    """One bounded JSON document, or one refusal naming the path."""
    try:
        raw = Path(place).read_bytes()
    except FileNotFoundError:
        raise PoolRefusal("there is nothing at " + str(place)
                          + ", and this verb reads " + what + " there. "
                          "Nothing was changed.")
    except OSError as failure:
        raise PoolRefusal(str(place) + " could not be read as " + what
                          + " (" + type(failure).__name__ + ": "
                          + str(failure) + "). Nothing was changed.")
    if len(raw) > limit:
        raise PoolRefusal(str(place) + " is wider than " + str(limit)
                          + " bytes, which is not " + what
                          + ". Nothing was changed.")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as failure:
        raise PoolRefusal(str(place) + " is not one UTF-8 JSON document ("
                          + type(failure).__name__ + ": " + str(failure)
                          + "). Nothing was changed.")
    if type(document) is not dict:
        raise PoolRefusal(str(place) + " holds " + type(document).__name__
                          + " and " + what + " is one JSON object. Nothing "
                          "was changed.")
    return document


def read_configuration(place):
    """The `deployment.json` this instance is already serving under."""
    return _read(place, stage_execution.MAX_CONFIG_BYTES,
                 "an instance's deployment configuration")


def read_worker(place):
    """The one worker document to admit, in the shape an input names one."""
    return _read(place, single_worker.MAX_CONFIG_BYTES,
                 "a worker document")


# -- what a worker document has to be -----------------------------------------


def held_worker(worker):
    """The worker's own wrapper, held to `tools.bootstrap`'s member set.

    ITS TUPLE, NOT A COPY OF IT. `bootstrap._WORKER` is what an input document
    names a worker with; a verb that admitted a differently-shaped one would be
    admitting something the install path could not have configured. The nested
    `deployment` is NOT examined here -- it is the single-worker launch
    document, and its own validator owns it, reached through `admit` below.
    """
    if type(worker) is not dict:
        raise PoolRefusal("a worker is one document, not "
                          + type(worker).__name__)
    found = sorted(name for name in worker if name not in bootstrap._WORKER)
    if found:
        raise PoolRefusal(
            "this worker cannot be admitted: nothing reads "
            + ", ".join(found) + ". A worker names exactly "
            + ", ".join(bootstrap._WORKER) + ", and a selection this verb "
            "cannot carry is refused rather than accepted and dropped.")
    absent = sorted(name for name in bootstrap._WORKER
                    if worker.get(name) in (None, "", {}))
    if absent:
        raise PoolRefusal(
            "this worker cannot be admitted: the following are not named and "
            "cannot be derived -- " + ", ".join(absent) + ".")
    # THE IDENTITY IS A NAME, held to bootstrap's own rule for one. An id an
    # installation could not have made a directory from is not one this verb
    # admits into the same pool.
    bootstrap._safe_name(worker["worker_id"])
    if worker["role"] not in bootstrap.ROLES:
        raise PoolRefusal(
            "this deployment serves " + ", ".join(bootstrap.ROLES)
            + " and this worker names the role " + repr(worker["role"]) + ".")
    return worker


def admitted(held, worker, principal):
    """The configured entry, with the five members a deployment fills in.

    EXACTLY THE FIVE `bootstrap.configuration` FILLS IN -- participant,
    principal, authority_store, authority_uuid and launch_role -- so a document
    written for an install and a document admitted here are the same document.

    THE INSTANCE'S OWN CONFIGURATION IS WHERE THE STORE AND THE IDENTITY COME
    FROM, rather than a layout re-derived from a root this verb was not given.
    `bootstrap.configuration` derives them from `state_root` because it is
    COMPOSING the instance; this one is amending an instance that has already
    said where its Authority is, and re-deriving would be a second answer to a
    question the file in hand already answers.
    """
    return {"worker_id": worker["worker_id"], "role": worker["role"],
            "deployment": dict(worker["deployment"],
                               participant=worker["participant"],
                               principal=principal,
                               authority_store=held["authority_store"],
                               authority_uuid=held["authority_uuid"],
                               launch_role=worker["role"])}


# -- the generation the scheduler will mint -----------------------------------


def job_store_of(held):
    """This instance's Job store, beside the Authority store it names."""
    return os.path.join(os.path.dirname(held["authority_store"]),
                        JOB_STORE_NAME)


def minted_generation(held, proved, *, store=None):
    """Which generation `activate_pool` WOULD answer, read and not decided.

    THE SCHEDULER'S RULE, ASKED RATHER THAN RESTATED, and it is the one
    `stage_execution._pool_generation` already applies at activation: an absent
    pool means the next activation mints generation 1, the ACTIVE generation's
    digest matching this document means the next activation is a revalidation
    of it, and anything else is the next generation. Admitting a worker changes
    the pool document, so an instance with an active pool moves on by one --
    but that is the rule's answer here rather than an assumption about it, and
    a caller re-running this verb after a failed write gets the truth.

    THE POOL IS `stage_execution`'S OWN. `_pool` is the immutable document this
    configuration IS, and `own_pool` is the scheduler's own reading of one --
    including the rules `held_configuration` does not make, such as one
    participant per pool. Composing a second idea of either here is how the
    printed number and the activated one would come to disagree.

    NOTHING IS OPENED FOR WRITING. A Job store that does not exist is an
    instance whose scheduler has never run, and this answers 1 for it rather
    than creating the store to find out.
    """
    from baton_v12.job_manager import scheduler

    pool = scheduler.own_pool(stage_execution._pool(proved, None))
    if store is not None:
        return _would(pool, scheduler.active_generation(store))
    place = job_store_of(held)
    if not os.path.isfile(place):
        return _would(pool, None)
    from baton_v12.job_manager import JobStore

    opened = JobStore.open_readonly(
        place, authority_uuid=held["authority_uuid"],
        # THE INSTANT SOURCE THIS BUILD ALREADY COMPOSES. A second spelling of
        # "now" beside the one `stage_execution` hands every store it opens is
        # a second thing to keep in step with the journal's format.
        incarnation=INCARNATION, clock=stage_execution._now)
    try:
        return _would(pool, scheduler.active_generation(opened))
    finally:
        opened.close()


def _would(pool, active):
    """The scheduler's own three-way answer, over one owned pool document."""
    from baton_v12.contracts import digest

    if active is None:
        return 1
    if active["digest"] == digest(pool):
        return active["generation"]
    return active["generation"] + 1


# -- the admission ------------------------------------------------------------


def admit(place, worker, *, stream=sys.stdout, opener=None, store=None):
    """Prove everything, then replace one file. In that order.

    The return is what was proved and what was written, so a caller that is not
    a command line does not have to read the file back to learn either.
    """
    held = read_configuration(place)
    worker = held_worker(worker)

    for name in ("schema", "authority_store", "authority_uuid", "workers"):
        if name not in held:
            raise PoolRefusal(
                str(place) + " is not an instance's deployment configuration: "
                "it names no " + name + ". Nothing was changed.")
    # THE ONE-JOB VARIANT SERVES EXACTLY ONE WORKER PER ROLE, so every worker
    # this verb could admit to one is a worker `_held_workers` refuses. Saying
    # so here names the variant and the way out; letting the accepted validator
    # say it would name only the duplicated role, and would send an operator
    # looking for a worker they did not configure.
    if held["schema"] == stage_execution.CONFIG_SCHEMA:
        raise PoolRefusal(
            "this instance is configured as " + stage_execution.CONFIG_SCHEMA
            + ", which serves exactly one worker per role, so there is no "
            "worker this verb could admit to it. Nothing here rewrites a "
            "deployment's schema -- a " + stage_execution.MULTI_CONFIG_SCHEMA
            + " document says its Job bindings out loud, and moving between "
              "the two is a decision about what this deployment BINDS rather "
              "than about its capacity. Nothing was changed.")
    if type(held["workers"]) is not list:
        raise PoolRefusal(
            str(place) + " names its workers as "
            + type(held["workers"]).__name__ + " rather than a list. Nothing "
            "was changed.")

    # THE POOL TELLS ITS WORKERS APART BY THEIR IDENTITY, so one already
    # configured is refused rather than appended beside its namesake. This is
    # `_held_workers`' own rule, made here so the refusal names the instance
    # the identity is already in rather than an amended document the operator
    # never wrote.
    configured = [one.get("worker_id") for one in held["workers"]
                  if type(one) is dict]
    if worker["worker_id"] in configured:
        raise PoolRefusal(
            "worker " + repr(worker["worker_id"]) + " is already configured "
            "in " + str(place) + "; the pool tells its workers apart by that "
            "identity and cannot hold it twice. Nothing here replaces a "
            "configured worker -- admit the new capacity under its own "
            "identity, or edit the instance's deployment if you mean to "
            "change what that one is. Nothing was changed.")

    # THE PRINCIPAL IS THE AUTHORITY'S ANSWER, not the document's. Whatever the
    # supplied deployment carries is discarded: `principal_of` is a read that
    # writes nothing, and it is the same resolution `bootstrap.principals_for`
    # performs for every worker an installation configures.
    places = {"authority_store": held["authority_store"]}
    if not Path(places["authority_store"]).exists():
        raise PoolRefusal(
            "this configuration names the Authority at "
            + str(places["authority_store"]) + " and there is nothing there, "
            "so a participant's principal cannot be resolved. A worker is "
            "admitted into an instance that has already been installed. "
            "Nothing was changed.")
    principals = bootstrap.principals_for(
        places,
        {"workers": [worker], "authority_uuid": held["authority_uuid"],
         "receipt_participants": held.get("receipt_participants") or {},
         "integration_profile": held.get("integration_profile") or {}},
        opener=opener)

    entry = admitted(held, worker, principals[worker["participant"]])
    candidate = dict(held, workers=list(held["workers"]) + [entry])
    # THE ACCEPTED VALIDATOR, WHOLE, over the amended document -- which is
    # where the manifest comparison, the profile shape, the launch-role
    # agreement, the outside-the-checkout paths and the review independence
    # are all held. `bootstrap.validated` is called rather than
    # `held_configuration` directly so the refusal an operator reads is the
    # one the install path would have given them.
    proved = bootstrap.validated(candidate)

    minted = minted_generation(held, proved, store=store)
    written = dict(candidate, pool_generation=minted)
    if minted != candidate.get("pool_generation"):
        # PROVED AS IT WILL BE WRITTEN. The generation moved after the document
        # above was held, and a validator that was shown a different document
        # from the one that is published proves nothing about the published one.
        bootstrap.validated(written)

    # -- and only now ---------------------------------------------------
    bootstrap._publish(Path(place), written)

    print("worker    %-14s %s" % (entry["worker_id"], entry["role"]),
          file=stream)
    print("principal %-14s %s" % (entry["deployment"]["participant"],
                                  entry["deployment"]["principal"]),
          file=stream)
    print("pool      generation %d will be minted at the next activation"
          % minted, file=stream)
    print("configuration " + str(place), file=stream)
    print("no Job was prepared, nothing was submitted, no Work was created or "
          "touched, and no configured worker was removed or changed",
          file=stream)
    return {"configuration": written, "worker": entry,
            "pool_generation": minted, "held": proved,
            "principal": entry["deployment"]["principal"]}


# -- W321608: composing a worker document for THIS instance -------------------
#
# WHAT THIS IS FOR. A worker's `deployment` is the `/4` single-worker launch
# document, and it carries an `input_manifest` digest-sealed over the Authority
# and Work it serves, a `human_contract` naming the installed task bytes, and
# the paths the instance derives. Every installation to date composed one with
# a dossier script that copied a reviewed deployment and resealed it by hand,
# which OBS-0a names as a product gap: provisioning belongs to installation
# tooling, not to per-deployment scripts.
#
# WHERE THE FACTS COME FROM, and this is the whole design. The runtime profile,
# the execution policy and the adapter identity are THIS BUILD'S documents --
# `next_run_bindings.deployment_identities`, the same ones the standard
# next-run packet composes -- and the input manifest is the INSTALLED template
# (`contracts.frozen.input_manifest_template`, the published conformance
# vector's document shipped beside the schema assets) bound here through
# `next_run_bindings.input_manifest`; nothing is read from a dossier. What an
# operator names is ordinary configuration: the image, the CLI build, the
# network, the credential registry and slot mapping, the workspace group, the
# task document, and the worker's identity and role. Nothing is inherited from
# another instance's protocol documents.

VERB_COMPOSE = "compose-worker"
_SHA256 = "sha256:"
# Which route an answered candidate's assignment passes to, per role: the
# implementation's result goes to review; the review's verdict goes on to
# integration. `tests/tools/test_bootstrap.ValidFixture` and the standard
# next-run packet agree on these two values.
REVIEW_ROUTES = {"implementation": "rview", "review": "integration",
                 "integration": "owner"}


def _credential_profile(mappings):
    """`slot=provider:reference` operands, as the deployment's mapping."""
    profile = {}
    for one in mappings or ():
        if type(one) is not str or "=" not in one or ":" not in one.split("=", 1)[1]:
            raise PoolRefusal("a credential mapping is spelled "
                              "slot=provider:reference; this is " + repr(one)
                              + ". Nothing was changed.")
        slot, rest = one.split("=", 1)
        provider, reference = rest.split(":", 1)
        if not slot or not provider or not reference:
            raise PoolRefusal("a credential mapping names a slot, a provider "
                              "and a reference; this is " + repr(one)
                              + ". Nothing was changed.")
        if slot in profile:
            raise PoolRefusal("credential slot " + repr(slot) + " is mapped "
                              "twice. Nothing was changed.")
        profile[slot] = {"provider": provider, "reference": reference}
    if not profile:
        raise PoolRefusal("a worker names at least one credential slot "
                          "mapping (slot=provider:reference). Nothing was "
                          "changed.")
    return profile


def _task_artifact(place):
    """The installed task bytes this worker is sealed over, read once."""
    try:
        raw = Path(place).read_bytes()
    except (FileNotFoundError, OSError) as failure:
        raise PoolRefusal("the task document " + str(place) + " could not be "
                          "read (" + type(failure).__name__ + "); a worker is "
                          "sealed over task bytes that exist. Nothing was "
                          "changed.")
    if len(raw) > single_worker.MAX_TASK_BYTES:
        raise PoolRefusal("the task document " + str(place) + " is wider "
                          "than " + str(single_worker.MAX_TASK_BYTES)
                          + " bytes, which the worker refuses. Nothing was "
                          "changed.")
    try:
        held = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise PoolRefusal("the task document " + str(place) + " is not one "
                          "UTF-8 JSON document. Nothing was changed.")
    if type(held) is not dict or type(held.get("task_id")) is not str \
            or not held["task_id"]:
        raise PoolRefusal("the task document " + str(place) + " names no "
                          "task_id; the worker's human-contract artifact is "
                          "named after it. Nothing was changed.")
    return raw, held["task_id"]


def composed(held, *, worker_id, role, participant, image_reference,
             image_digest, cli_build, network, credential_sources,
             credentials, workspace_group, task_document, work_id=None,
             runtime_uid=None):
    """One worker document for the instance `held` describes. READS ONLY.

    Every member the instance binds is derived from the instance; every
    deployment fact is this build's own (`next_run_bindings`); what the
    operator named is ordinary configuration. The manifest is resealed by
    §12's rule and proved by the accepted structure check before anything is
    returned. The derived paths are the ones `bootstrap` derives for a worker
    named at install, so one document serves both the repeated bootstrap that
    clones its source and `add-worker` once that source exists.
    """
    from baton_v12.contracts.manifest import check_manifest_structure
    from baton_v12.job_manager import execution_limits
    from tools import instance, next_run_bindings

    for name in ("authority_store", "authority_uuid", "state_root",
                 "retention_policy_digest", "retention_disposition"):
        if not held.get(name):
            raise PoolRefusal("this is not an instance's deployment "
                              "configuration: it names no " + name
                              + ". Nothing was changed.")
    bootstrap._safe_name(worker_id)
    if role not in REVIEW_ROUTES or role not in bootstrap.ROLES:
        raise PoolRefusal("this deployment serves " + ", ".join(bootstrap.ROLES)
                          + " and this worker names the role " + repr(role)
                          + ". Nothing was changed.")
    for name, value in (("participant", participant),
                        ("image_reference", image_reference),
                        ("cli_build", cli_build), ("network", network)):
        if type(value) is not str or not value:
            raise PoolRefusal("a worker names one " + name + ". Nothing was "
                              "changed.")
    if type(image_digest) is not str or not image_digest.startswith(_SHA256) \
            or len(image_digest) != len(_SHA256) + 64:
        raise PoolRefusal("an image digest is sha256: followed by 64 hex "
                          "characters; this is " + repr(image_digest)
                          + ". Nothing was changed.")
    if type(workspace_group) is not int or workspace_group <= 0:
        raise PoolRefusal("the workspace group is one positive group id; this "
                          "is " + repr(workspace_group) + ". Nothing was "
                          "changed.")
    for name, place in (("credential registry", credential_sources),
                        ("task document", task_document)):
        if type(place) is not str or not os.path.isabs(place):
            raise PoolRefusal("the " + name + " is named by an absolute path; "
                              "this is " + repr(place) + ". Nothing was "
                              "changed.")
    destination = Path(held["state_root"]).parent
    places = instance.layout(destination)
    if places["authority_store"] != held["authority_store"]:
        raise PoolRefusal(
            "this configuration's state_root " + str(held["state_root"])
            + " does not sit in the destination whose Authority store is "
            + str(held["authority_store"]) + ", so the instance's paths "
            "cannot be derived. Nothing was changed.")
    profile = _credential_profile(credentials)
    work = work_id or held.get("job_work_id") or (held["authority_uuid"][:8]
                                                 + "-W1")
    raw, task_id = _task_artifact(task_document)
    limits = execution_limits.resolved(None)["boundaries"]
    try:
        identities = next_run_bindings.deployment_identities(
            image_reference=image_reference, image_digest=image_digest,
            cli_build=cli_build, provider_network=network,
            runtime_uid=runtime_uid,
            turn_seconds=limits["provider_turn"]["seconds"],
            verification_seconds=limits["ordinary_verification"]["seconds"],
            implementer_invocations=1, contextual=False)
        manifest = next_run_bindings.input_manifest(
            None, authority_uuid=held["authority_uuid"], work_id=work,
            policy_digest=identities["policy_digest"],
            profile_digest=identities["profile_digest"],
            image_digest=image_digest, task_bytes=raw, artifact_id=task_id,
            contextual=False)
        manifest = check_manifest_structure(manifest, "inputManifest",
                                            what="the composed input manifest")
    except (next_run_bindings.BindingRefusal, Exception) as failure:  # noqa: BLE001
        raise PoolRefusal("the worker could not be composed from this build's "
                          "documents: " + str(failure) + ". Nothing was "
                          "changed.")
    deployment = {
        "schema": single_worker.CONFIG_SCHEMA,
        "profile_name": identities["runtime_profile"]["name"],
        "profile_digest": identities["profile_digest"],
        "policy_digest": identities["policy_digest"],
        "adapter_name": identities["adapter"]["adapter_name"],
        "adapter_digest": identities["adapter_digest"],
        "engine": "docker", "image_digest": image_digest, "network": network,
        # ONE WORKSPACE ROOT PER INSTANCE: the creation derivation guards the
        # instance as one root and refuses workers naming two, so every worker
        # of an instance shares `state/workspaces`, as the accepted
        # deployments and the standard next-run packet do.
        "workspace_storage": os.path.join(places["state"], "workspaces"),
        "workspace_group": workspace_group,
        "launch_home": os.path.join(places["state"], "launch"),
        "credential_home": os.path.join(places["state"], "credentials"),
        "credential_sources": credential_sources,
        "credential_slots": sorted(profile),
        "credential_profile": profile,
        "nominated_source": os.path.join(places["repository"],
                                         "source-" + worker_id),
        "workspace_capacity": {
            "max_bytes":
                identities["runtime_profile"]["workspace_min_bytes"]},
        "input_manifest": manifest,
        "task_document": str(task_document),
        "launch_contract": "v12-assignment-1",
        "review_route": REVIEW_ROUTES[role],
        "retention_policy_digest": held["retention_policy_digest"],
        "retention_disposition": held["retention_disposition"]}
    worker = held_worker({"worker_id": worker_id, "role": role,
                          "participant": participant,
                          "deployment": deployment})
    return {"worker": worker, "work_id": work,
            "manifest_digest": manifest["manifest_digest"],
            "human_contract": manifest["human_contract"],
            "identities": {"profile_digest": identities["profile_digest"],
                           "policy_digest": identities["policy_digest"],
                           "adapter_digest": identities["adapter_digest"]}}


def _written_fresh(target, body):
    """ONE NEW FILE, created exclusively at the filesystem operation.

    Review 2026-11-19T02-52-40Z: an existence check followed by a write
    followed a dangling symlink and wrote elsewhere. `O_CREAT|O_EXCL|
    O_NOFOLLOW` makes the kernel the judge: any existing entry -- a file, a
    directory, a symlink whether or not it resolves, or one that appeared
    between this call and a concurrent one -- is refused, and nothing that
    was there is touched.
    """
    target = Path(target)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(str(target),
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW, 0o644)
    except FileExistsError:
        raise PoolRefusal(str(target) + " already exists (as a file, a "
                          "directory or a symbolic link, resolving or not); "
                          "this verb writes a fresh worker document and never "
                          "replaces or follows one. Nothing was changed.")
    except OSError as failure:
        raise PoolRefusal(str(target) + " could not be created ("
                          + type(failure).__name__ + "). Nothing was changed.")
    with os.fdopen(descriptor, "w", encoding="utf-8") as writing:
        writing.write(body)
    return str(target)


def compose(place, *, into, stream=sys.stdout, admit_into_pool=False,
            **selection):
    """Compose, write ONE new file, and only then -- if asked -- admit."""
    held = read_configuration(place)
    answer = composed(held, **selection)
    body = json.dumps(answer["worker"], indent=1, sort_keys=True) + "\n"
    written = _written_fresh(into, body)
    worker = answer["worker"]
    print("worker    %-14s %s" % (worker["worker_id"], worker["role"]),
          file=stream)
    print("work      %s" % answer["work_id"], file=stream)
    print("image     %s" % worker["deployment"]["image_digest"], file=stream)
    print("profile   %s %s" % (worker["deployment"]["profile_name"],
                               worker["deployment"]["profile_digest"]),
          file=stream)
    print("task      %s (%s)" % (worker["deployment"]["task_document"],
                                 answer["human_contract"]["artifact_id"]),
          file=stream)
    print("manifest  %s" % answer["manifest_digest"], file=stream)
    print("written   %s" % written, file=stream)
    print("no Job was prepared, nothing was submitted, no Work was created or "
          "touched, and the instance's configuration was not changed",
          file=stream)
    if admit_into_pool:
        answer["admitted"] = admit(place, worker, stream=stream)
    return dict(answer, written=written)


def main(argv=None, *, stream=sys.stdout):
    parser = argparse.ArgumentParser(
        prog="pool",
        description="Compose a worker document for an installed instance, "
                    "or admit one into its pool.")
    verbs = parser.add_subparsers(dest="verb", required=True)
    adding = verbs.add_parser(
        VERB, help="admit one worker document into an instance's deployment "
                   "configuration; no Job is prepared and nothing is submitted")
    adding.add_argument("--deployment", required=True,
                        help="the instance's deployment.json, as "
                             "tools.bootstrap wrote it")
    adding.add_argument("--worker", required=True,
                        help="the one worker document to admit, naming "
                             + ", ".join(bootstrap._WORKER))
    composing = verbs.add_parser(
        VERB_COMPOSE,
        help="compose one worker document for an installed instance from "
             "this build's own runtime profile, policy, adapter and manifest "
             "vector plus ordinary operator configuration; writes one fresh "
             "file and changes nothing")
    composing.add_argument("--deployment", required=True,
                           help="the instance's deployment.json")
    composing.add_argument("--worker-id", required=True)
    composing.add_argument("--role", required=True, choices=bootstrap.ROLES)
    composing.add_argument("--participant", required=True)
    composing.add_argument("--image-reference", required=True,
                           help="the worker image as named to the engine, "
                                "e.g. baton-v12-worker:f34e1576")
    composing.add_argument("--image-digest", required=True,
                           help="its immutable digest, sha256:…")
    composing.add_argument("--cli-build", required=True,
                           help="the provider CLI build the image carries, "
                                "as the recipe pins it")
    composing.add_argument("--network", required=True,
                           help="the approved OCI network name")
    composing.add_argument("--credential-sources", required=True,
                           help="absolute path of the private credential "
                                "registry")
    composing.add_argument("--credential", action="append", required=True,
                           metavar="SLOT=PROVIDER:REFERENCE",
                           help="one credential slot mapping, repeatable")
    composing.add_argument("--workspace-group", required=True, type=int,
                           help="the provisioned workspace group id")
    composing.add_argument("--task-document", required=True,
                           help="absolute path of the installed task document "
                                "this worker is sealed over")
    composing.add_argument("--work-id", default=None,
                           help="the Work this worker serves; omitted, the "
                                "instance's own Work")
    composing.add_argument("--into", required=True,
                           help="the fresh file to write the worker document "
                                "to; an existing entry is refused")
    composing.add_argument("--admit", action="store_true",
                           help="also admit it into the instance's pool "
                                "(needs the nominated source to exist)")
    taken = parser.parse_args(argv)
    try:
        if taken.verb == VERB_COMPOSE:
            compose(taken.deployment, into=taken.into, stream=stream,
                    admit_into_pool=taken.admit, worker_id=taken.worker_id,
                    role=taken.role, participant=taken.participant,
                    image_reference=taken.image_reference,
                    image_digest=taken.image_digest,
                    cli_build=taken.cli_build, network=taken.network,
                    credential_sources=taken.credential_sources,
                    credentials=taken.credential,
                    workspace_group=taken.workspace_group,
                    task_document=taken.task_document,
                    work_id=taken.work_id)
            return 0
        admit(taken.deployment, read_worker(taken.worker), stream=stream)
        return 0
    except PoolRefusal as refusal:
        print("refused: " + str(refusal), file=stream)
        return 2


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
