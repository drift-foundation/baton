"""One deployed v12 instance, selected by one file. W183883.

OWNER-INSTANCE-DESTINATION-20260916.md and OWNER-PYINSTALLER-20260916.md:
`bootstrap inputs.json /absolute/external/dest` prepares an installed runtime
there and emits `instance.json`; `start`, `stop`, `status` and `monitor` take
THAT SAME FILE and derive every state, store, log and process path from it. The
four manual exports and the global state-root default are superseded.

    destination/
      distro/         the bundled command, its Python, libraries and resources
      instance.json   the one lifecycle selector
      db/             authority, Job, control and integration stores
      repo/           the independent Job repository
      logs/           logs and the published observation
      state/          process records, snapshots and other mutable execution

WHY THE IDENTITY IS A MANIFEST AND NOT A CHECKSUM OF THE EXECUTABLE. A
one-folder bundle is a DIRECTORY: the launcher is a small bootloader and the
interpreter, the libraries and the frozen resources sit beside it. An instance
that recorded only the executable's digest would be satisfied by a distro whose
`rpds` native library had been replaced or whose schema assets had been deleted
-- and the second of those fails at import, which is to say at the worst moment.
So the instance binds EVERY file under `distro/`, and `verify` recomputes them.

NOTHING HERE UPGRADES ANYTHING. A destination already holding a different
distro, a different Authority or a different deployment is REFUSED, with what
differs named. Safe refusal is the whole answer the owner selected; there is no
migration or repair interface, and a running stack is never overwritten.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

SCHEMA = "baton.v12.stack-instance/1"
FILENAME = "instance.json"

# The one-folder runtime, and the four directories an instance owns beside it.
DISTRO = "distro"
STORES = "db"
REPOSITORY = "repo"
LOGS = "logs"
STATE = "state"


class InstanceRefusal(Exception):
    """An operator-facing refusal. Its text is the whole message."""


def layout(destination):
    """Every path an instance owns, derived from the one root it was given.

    DERIVED, NEVER CONFIGURED TWICE. An operator names the destination; where
    the stores, the logs and the process records live under it is this layout's
    answer, so no two documents can disagree about it.
    """
    root = Path(destination)
    return {
        "destination": str(root),
        "instance": str(root / FILENAME),
        "distro": str(root / DISTRO),
        "command": str(root / DISTRO / "baton-v12-stack"),
        "stores": str(root / STORES),
        "authority_store": str(root / STORES / "authority.sqlite3"),
        "job_store": str(root / STORES / "jobs.sqlite3"),
        "control_store": str(root / STORES / "control.sqlite3"),
        "integration_store": str(root / STORES / "integration.sqlite3"),
        "repository": str(root / REPOSITORY),
        "logs": str(root / LOGS),
        "state": str(root / STATE),
        "deployment": str(root / "deployment.json"),
        "record": str(root / "bootstrap.json"),
        # The stage deployment's own mutable root, which `tools.bootstrap`
        # derives identically. It is NOT `state/`: that is this stack's process
        # records, and one path for two different things is how they collide.
        "deployment_state": str(root / "deployment-state"),
        # WHERE COOPERATING BOOTSTRAPS SERIALIZE. A destination is prepared
        # once, and two attempts preparing it at the same time would interleave
        # a copy and a publication; `tools.bootstrap` holds this exclusively
        # across both. It is an owned name like any other, so a link left at it
        # is refused rather than opened.
        "lock": str(root / ".bootstrap.lock"),
        # THE DEPLOYED INTERFACE. OWNER-STANDALONE-INTERFACE-20260916.md:
        # "once deployed, we shouldn't have to require more than the
        # destination for stop/start/status". `just` in the destination, or
        # `just --justfile <destination>/justfile` from anywhere, is that
        # interface; it resolves everything from its OWN directory.
        "justfile": str(root / "justfile"),
    }


# -- what the runtime IS ------------------------------------------------------


def manifest(distro):
    """Every file under the one-folder runtime, with its digest.

    THE WHOLE FOLDER, for the reason in the module docstring: a bundle is a
    directory and its libraries and resources are as load-bearing as its
    launcher. Symlinks are recorded as their target text rather than followed,
    so a distro that replaced a real library with a link to somewhere else is a
    DIFFERENT distro rather than the same one.
    """
    root = Path(distro)
    if root.is_symlink():
        # [K2]: every link INSIDE the bundle was bound, and the root itself was
        # not -- so a `distro` that was a link to another tree digested that
        # tree and called it this one.
        raise InstanceRefusal(
            "the bundled runtime at " + str(root) + " is itself a link to "
            + os.path.realpath(root) + "; a bundle is the directory it is, not "
            "a name pointing at one somebody else can move.")
    if not root.is_dir():
        raise InstanceRefusal("there is no bundled runtime at " + str(root))
    held = os.path.realpath(root)
    files = {}
    for place in sorted(root.rglob("*")):
        relative = str(place.relative_to(root))
        if place.is_symlink():
            # [K2]: recording only the LINK TEXT left an external link's target
            # free to change while the manifest stayed identical -- the bytes
            # that would actually be loaded were outside everything this binds.
            # A link inside the bundle is safe and is recorded as its text; one
            # pointing out of it, or at nothing, is refused rather than bound.
            target = os.path.realpath(place)
            if not os.path.exists(place):
                raise InstanceRefusal(
                    "the bundled runtime at " + str(root) + " carries a broken "
                    "link at " + relative + "; what it would load cannot be "
                    "established")
            if target != held and not target.startswith(held.rstrip("/") + "/"):
                raise InstanceRefusal(
                    "the bundled runtime at " + str(root) + " carries a link at "
                    + relative + " pointing outside it, to " + target
                    + ". A bundle whose bytes live somewhere else is "
                    "not self-contained, and its target could change while "
                    "this manifest did not.")
            files[relative] = "link:" + os.readlink(place)
        elif place.is_file():
            files[relative] = hashlib.sha256(place.read_bytes()).hexdigest()
        elif not place.is_dir():
            raise InstanceRefusal(
                "the bundled runtime at " + str(root) + " carries " + relative
                + ", which is neither a file, a directory nor a link; this "
                "binds what it can digest and refuses what it cannot")
    if not files:
        raise InstanceRefusal("the bundled runtime at " + str(root) + " is empty")
    listing = "\n".join("%s %s" % (name, files[name]) for name in sorted(files))
    return {"files": len(files),
            "digest": hashlib.sha256(listing.encode()).hexdigest(),
            "entries": files}


def emit(destination, *, authority_uuid, identity, runtime, now=None):
    """The document every lifecycle command will be given."""
    places = layout(destination)
    return {
        "schema": SCHEMA,
        "destination": places["destination"],
        "command": places["command"],
        "authority_uuid": authority_uuid,
        "deployment": places["deployment"],
        "job_store": places["job_store"],
        "control_store": places["control_store"],
        "state": places["state"],
        "logs": places["logs"],
        "repository": places["repository"],
        # WHAT WAS BUILT, recorded rather than assumed: a one-folder bundle is
        # host-specific, and an instance that could not say which build it holds
        # could not tell a replaced runtime from its own.
        "identity": identity,
        "runtime": {"files": runtime["files"], "digest": runtime["digest"]},
        "prepared_at": now,
    }


_MEMBERS = ("schema", "destination", "command", "authority_uuid", "deployment",
            "job_store", "control_store", "state", "logs", "repository",
            "identity", "runtime")


def malformed(document, place):
    """Why this is not an instance selector, or None."""
    if type(document) is not dict:
        return ("an instance selector is one document, not "
                + type(document).__name__)
    if document.get("schema") != SCHEMA:
        return ("this reads " + SCHEMA + " and " + str(place) + " is "
                + repr(document.get("schema")))
    absent = [name for name in _MEMBERS if document.get(name) in (None, "", {})]
    if absent:
        return str(place) + " does not name " + ", ".join(sorted(absent))
    for name in ("destination", "command", "deployment", "job_store",
                 "control_store", "state", "logs", "repository"):
        # [K1]: `isabs` on a non-string raised TypeError out of a validator
        # whose whole job is to turn a bad document into a refusal.
        if type(document[name]) is not str:
            return (str(place) + " names " + name + " as "
                    + type(document[name]).__name__ + "; every path an instance "
                    "owns is text")
        if not os.path.isabs(document[name]):
            return (str(place) + " names a relative " + name + "; an instance "
                    "is addressed absolutely or it is addressed differently "
                    "from wherever a command happened to run")
    runtime = document["runtime"]
    if type(runtime) is not dict or type(runtime.get("digest")) is not str \
            or type(runtime.get("files")) is not int or runtime["files"] < 1:
        return str(place) + " does not record what runtime it was prepared with"
    return None


def read(place):
    """One instance selector, validated before anything is derived from it."""
    place = Path(place)
    try:
        document = json.loads(place.read_bytes())
    except FileNotFoundError:
        raise InstanceRefusal(
            "there is no instance at " + str(place) + ". `just bootstrap "
            "<inputs.json> <destination>` prepares one and writes it there.")
    except (ValueError, OSError) as failure:
        raise InstanceRefusal(str(place) + " could not be read as an instance ("
                              + type(failure).__name__ + "), so nothing was "
                              "derived from it")
    problem = malformed(document, place)
    if problem is not None:
        raise InstanceRefusal(problem)
    # AND IT HAS TO BE THE INSTANCE AT THIS PATH. A selector copied somewhere
    # else still names the destination it was prepared for, and following it
    # would drive that other deployment from here without saying so.
    held = os.path.realpath(place.parent)
    named = os.path.realpath(document["destination"])
    if held != named:
        raise InstanceRefusal(
            str(place) + " was prepared for " + named + " and is being read "
            "from " + held + "; an instance selector names its own destination, "
            "and a copied one would drive somebody else's deployment. Use the "
            "selector that is in the destination you mean.")
    # [K1]: only the destination was compared, so a selector kept at A with A's
    # valid runtime but B's state, stores, configuration and logs passed -- and
    # `stop` went to B's state root. Every path IS the layout's, so every path
    # is compared to the layout rather than believed.
    places = layout(document["destination"])
    for name, derived in (("command", "command"), ("deployment", "deployment"),
                          ("job_store", "job_store"),
                          ("control_store", "control_store"),
                          ("state", "state"), ("logs", "logs"),
                          ("repository", "repository")):
        if document[name] != places[derived]:
            raise InstanceRefusal(
                str(place) + " names " + name + " " + repr(document[name])
                + " and this destination derives " + repr(places[derived])
                + "; every path an instance owns is DERIVED from its "
                "destination, so one that disagrees is describing a different "
                "deployment.")
        # AND IT HAS TO RESOLVE INSIDE THE DESTINATION. [K1]: comparing
        # realpaths made `A/state` symlinked to `B/state` compare EQUAL to
        # itself -- both sides resolved to B -- so an unchanged selector
        # dispatched `stop` into another instance. Equality is not containment,
        # and a path that leaves the destination is not this instance's.
        resolved = os.path.realpath(places[derived])
        if resolved != held and not resolved.startswith(held.rstrip("/") + "/"):
            raise InstanceRefusal(
                str(place) + " derives " + name + " " + repr(places[derived])
                + ", which resolves to " + resolved + " -- outside this "
                "instance at " + held + ". An instance owns what is under its "
                "own destination; a link out of it is another deployment.")
    return document


def verify(document):
    """Is the runtime this instance was prepared with still the one that is here?

    RECOMPUTED, NOT TRUSTED. `identity` exiting 0 says the command ran; it says
    nothing about whether the library beside it is the one this instance was
    built against, and a missing resource fails at import -- which is to say at
    the worst possible moment, inside a child a supervisor has already started.
    """
    places = layout(document["destination"])
    try:
        held = manifest(places["distro"])
    except InstanceRefusal as refusal:
        raise InstanceRefusal(
            "the runtime this instance names is not usable: " + str(refusal)
            + ". Nothing was started.")
    # [K2]: THE RUNTIME THAT IS ACTUALLY EXECUTING IS BOUND TOO. Verifying the
    # instance's own distro said nothing about which command was running: A's
    # executable, given B's selector, verified B's folder and then went on
    # dispatching children as A. When frozen, the running command must BE this
    # instance's.
    from tools import stack_command

    if stack_command.frozen():
        running = os.path.realpath(stack_command.executable())
        named = os.path.realpath(document["command"])
        if running != named:
            raise InstanceRefusal(
                "this command is " + running + " and the instance names "
                + named + "; a deployed command drives its OWN instance, and "
                "one build must not dispatch children on behalf of another.")
    if held["digest"] != document["runtime"]["digest"]:
        raise InstanceRefusal(
            "the runtime at " + places["distro"] + " is not the one this "
            "instance was prepared with: it holds " + str(held["files"])
            + " files digesting " + held["digest"][:16] + "... and the instance "
            "records " + str(document["runtime"]["files"]) + " digesting "
            + document["runtime"]["digest"][:16] + "... Nothing here upgrades a "
            "deployment in place; prepare a new destination.")
    return held


def settings(document):
    """The operands the lifecycle already reads, derived from the instance.

    The four exports are superseded as the SELECTION interface; they are still
    the vocabulary `tools.stack` speaks, so this translates rather than
    introducing a second one.
    """
    return {"BATON_V12_JOB_STORE": document["job_store"],
            "BATON_V12_CONTROL_STORE": document["control_store"],
            "BATON_V12_AUTHORITY_UUID": document["authority_uuid"],
            "BATON_V12_STAGE_EXECUTION_CONFIG": document["deployment"]}


def _owned(place, document):
    """A fresh, exclusively created regular file beside `place`, holding it.

    THE TEMPORARY IS OWNED BEFORE IT IS WRITTEN. Review 2026-09-16T13-20-49Z:
    writing a FIXED name -- `instance.json.new` -- meant writing through
    whatever was already at it. A symlink left there redirected the write into
    a foreign document and then published a SYMLINK as the selector; a hardlink
    to an existing selector destroyed that selector's bytes while publication
    went on to refuse and say it had left them alone.

    `mkstemp` creates with O_EXCL and O_NOFOLLOW semantics under a name nobody
    else holds, so there is nothing to check and nothing to race: the file
    written through this descriptor is one this attempt made. A pre-existing
    entry at any other name is neither followed, truncated, reused nor removed
    -- an unknown entry is somebody else's, and that is the whole rule.
    """
    handle, temporary = tempfile.mkstemp(prefix=".instance-", suffix=".new",
                                         dir=str(Path(place).parent))
    try:
        with os.fdopen(handle, "w") as writing:
            writing.write(json.dumps(document, indent=2, sort_keys=True) + "\n")
    except BaseException:
        _discard(temporary)
        raise
    return temporary


def _discard(temporary):
    """Remove ONLY the temporary this attempt created."""
    try:
        os.unlink(temporary)
    except OSError:                                          # pragma: no cover
        pass


def publish(place, document):
    """Atomically, so an interrupted write cannot leave a partial selector.

    THIS REPLACES WHATEVER IS THERE. It is how an instance's own selector is
    rewritten in place; a FIRST publication uses `create`, which refuses to
    replace anything.
    """
    place = Path(place)
    temporary = _owned(place, document)
    try:
        os.replace(temporary, place)
    except BaseException:
        _discard(temporary)
        raise


def create(place, document):
    """Publish a selector that cannot replace one that is already there.

    `os.replace` is atomic for a REPLACEMENT, which is exactly what must not
    happen when another writer's selector appeared while this bootstrap was
    preparing: review 2026-09-16T13-09-22Z showed install overwriting one.
    The content is written beside the name and then LINKED into it -- one
    atomic operation that fails if the name exists, rather than a check
    followed by a write that another attempt can slip between.

    A name that is already there is left EXACTLY as it was, bytes and links
    alike. Nothing here decides that somebody else's selector is stale.
    """
    place = Path(place)
    temporary = _owned(place, document)
    try:
        os.link(temporary, place)
    except FileExistsError:
        raise InstanceRefusal(
            "there is already an instance selector at " + str(place)
            + ", which appeared while this one was being prepared. It was left "
            "exactly as it was and nothing was published; an instance is "
            "prepared once, and whichever attempt got there first owns it.")
    finally:
        _discard(temporary)


# -- what a recipe needs to ask --------------------------------------------


ANSWERS = ("command", "destination", "state", "logs", "repository")


def main(argv=None, *, stream=sys.stdout):
    """One question about a prepared instance, answered from the selector.

    W183883: the lifecycle recipes need the INSTALLED command's path to run a
    deployment without the development checkout, and deriving it in shell would
    be a second place for what `layout` already owns -- two derivations that
    disagree are two deployments sharing a name. The selector is validated
    first, so a recipe cannot be handed a path out of a document this module
    would refuse.
    """
    parser = argparse.ArgumentParser(
        prog="instance",
        description="Answer one question about a prepared v12 instance.")
    parser.add_argument("question", choices=ANSWERS)
    parser.add_argument("instance",
                        help="the instance.json a bootstrap emitted")
    taken = parser.parse_args(argv)
    try:
        document = read(taken.instance)
        if taken.question == "command":
            # [K2] THE ANSWER TO THIS ONE IS EXECUTED. Review
            # 2026-09-16T13-36-58Z: `read` validates the SELECTOR -- its
            # members, the layout it derives and the containment of every path
            # -- and says nothing about the bytes at the end of them. The
            # recipes ran whatever this printed, so a changed launcher, a
            # changed library or an unbound extra file in the bundle was
            # executed and then, at best, noticed. A runtime cannot check its
            # own bytes after it has been loaded.
            verify(document)
        # AND THE OTHER ANSWERS ARE READS. `state` and `logs` are where an
        # operator looks when a deployment is broken, so a runtime that no
        # longer verifies must not also take away the means of finding out why.
        # Nothing executes those paths.
    except InstanceRefusal as refusal:
        print("refused: " + str(refusal), file=sys.stderr)
        return 2
    print(document[taken.question], file=stream)
    return 0


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
