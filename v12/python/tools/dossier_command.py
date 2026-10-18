"""The supported record surface: bind a dossier, read it, cite and RESOLVE its
evidence, and verify a retained instance's recovery set before admitting it.

W321688, the minimal provider under W39435, for the W321608 pilot.

WHY THIS IS A COMMAND AND NOT JUST AN API. The pilot assessment's finding is
that the installed stack exposes no canonical dossier binding at all -- an
operator standing a new v12 Work up had identities and history but no supported
way to say where its record lives, and `stack_command.COMMANDS` had no record
verb. An API nobody can reach from a deployed bundle is the same gap one layer
down, so this is registered as a subcommand of the installed command.

THE DIVISION OF LABOUR, which is the design decision in this file. The authority
stores the locator and the evidence references and NEVER OPENS A FILE: DB-1
forbids external I/O inside a store transaction, so filesystem resolution cannot
live in `core`. It lives here. `cite` digests a file and hands the authority the
digest; `verify` reads the citations back and compares them against a root. The
authority is the record of what is cited; this command is the only thing that
touches the bytes.

WHAT IT WILL NOT DO. It does not migrate a store, copy or restore a live
instance, clear a runtime hold, or admit a recovered instance as writable on its
own judgement -- `recovery-check` REPORTS and refuses; the admission is an
operator act. Slawomir is the production backup/restore authority and the sole
Git owner. `RECOVERY.md` in this Work's dossier is the procedure; this file is
the part of it a program can check.
"""
import argparse
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile

from tools import instance as instance_contract

__all__ = ["main"]

# The members a retained v12 instance needs for its state to mean anything
# again. Named as a CLOSED SET rather than discovered, because the failure this
# guards against is a recovery that restored three of four stores and looked
# complete: an authority holding assignments whose Job store is older is not a
# usable deployment, it is a deployment that will act on a state that never
# existed.
STORES = ("authority_store", "job_store", "control_store")

# The instance document this command will read, and the recovery set it emits.
INSTANCE_SCHEMA = "baton.v12.stack-instance/1"
RECOVERY_SCHEMA = "baton.v12.instance-recovery-set/3"

# The authority store's own marker, read from the restored file rather than
# assumed. A shared schema version number is not shared ownership.
AUTHORITY_STORE_KIND = "baton.v12.python.authority"

# The retained material a deployment's state means nothing without: its
# immutable inputs and outputs, provider contexts, workspaces and logs. Bound
# by content manifest -- see `_tree_member`.
RETAINED = ("state", "logs", "repository")

# SQLite's three sidecars. Their BYTES are bound, not their names: a `-wal`
# holding committed transactions is where a store's newest commits live.
SIDECARS = ("-wal", "-shm", "-journal")

# Members that are part of the set but are not stores: the configuration and
# version provenance that say WHICH BUILD wrote those rows. A store restored
# beside a different distro is the compatibility question this Work's schema
# boundary exists for, and a manifest that did not record it could not pose it.
# REQUIRED, and bound by value -- review P1 found them copied as optional
# fields nothing validated.
PROVENANCE = ("deployment", "identity", "runtime")

_READ_CHUNK = 1024 * 1024

# Review 2026-10-18T08-25-00Z P1. THE FOUR WAYS A REFERENCE FAILS TO RESOLVE,
# and they are four different facts rather than degrees of one.
#
# `escapes-root` is the one that review found and that this file previously
# could not say at all: a reference the authority accepts as relative, pointing
# at a SYMLINK whose target is outside the root, was opened, digested and
# reported `present`/intact. So out-of-root bytes were being certified as this
# dossier's evidence under this root, which is exactly the containment the
# relative grammar exists to promise.
EVIDENCE_PRESENT = "present"
EVIDENCE_ABSENT = "absent"
EVIDENCE_UNREADABLE = "unreadable"
EVIDENCE_ESCAPES = "escapes-root"
EVIDENCE_NOT_REGULAR = "not-a-regular-file"


def _digest_fd(descriptor):
    held = hashlib.sha256()
    while True:
        block = os.read(descriptor, _READ_CHUNK)
        if not block:
            break
        held.update(block)
    return "sha256:" + held.hexdigest()


def _digest(path):
    held = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(_READ_CHUNK)
            if not block:
                break
            held.update(block)
    return "sha256:" + held.hexdigest()


def _contained_read(root, reference):
    """Digest ONE contained regular file under `root`, or say why not.

    Returns `(state, digest, bytes)`; the digest is `None` unless `present`.

    THE CONTAINMENT ITSELF IS `_contained_open`, and this is the digesting
    caller of it. W321689 needed the same containment to hand back a file's
    BYTES rather than its digest -- a human integration record has to be read
    to be checked -- and a second descriptor-anchored walk written beside this
    one is how two copies of a containment rule drift apart. So the walk moved
    down one level and both callers share it.
    """
    state, descriptor = _contained_open(root, reference)
    if state != EVIDENCE_PRESENT:
        return state, None, None
    try:
        return state, _digest_fd(descriptor), os.fstat(descriptor).st_size
    except OSError:
        return EVIDENCE_UNREADABLE, None, None
    finally:
        os.close(descriptor)


def _contained_open(root, reference):
    """Open ONE contained regular file under `root`, or say why not.

    Returns `(state, descriptor)`; the descriptor is `None` unless `present`,
    and the CALLER owns it and closes it.

    WHY DESCRIPTOR ANCHORING AND NOT `lstat` PER COMPONENT. Review
    2026-10-18T08-48-00Z P1 closed the previous attempt with a real
    interleaving: that version checked every component with `lstat` and then
    opened the WHOLE PATHNAME, so `O_NOFOLLOW` protected only the last
    component. Rename `root/a` and put a symlink to an outside directory in its
    place between its `lstat` and the final `open`, and the open resolved
    through the new link and returned outside bytes as `present`. A static
    symlink test cannot establish race closure, and that one did not.

    SO THE PATH IS NEVER RE-RESOLVED BY NAME. Each directory component is
    OPENED with `O_DIRECTORY | O_NOFOLLOW` relative to the descriptor of the
    one before it, and the final component is opened relative to its parent's
    descriptor. A replacement after a component has been opened cannot change
    what that descriptor refers to, so there is no window between the check and
    the use: they are the same act.

    AND THE FINAL OPEN CANNOT BLOCK. `O_NONBLOCK` is set, because opening a
    FIFO for reading otherwise waits for a writer -- a recovery or verification
    command that hung on a named pipe somebody left in a tree would be a denial
    of service dressed as a check. The descriptor is `fstat`ed and anything but
    a regular file is refused, so the flag changes no accepted outcome.
    """
    directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) \
        | getattr(os, "O_NOFOLLOW", 0)
    try:
        anchor = os.open(root, directory_flags)
    except NotADirectoryError:
        # A ROOT THAT IS ITSELF A LINK is refused rather than followed: the
        # caller named a root and everything resolves inside THAT directory.
        # Linux answers ENOTDIR for `O_DIRECTORY|O_NOFOLLOW` on a symlink, so
        # the one check distinguishes the two.
        try:
            if stat.S_ISLNK(os.lstat(root).st_mode):
                return EVIDENCE_ESCAPES, None
        except OSError:
            pass
        return EVIDENCE_NOT_REGULAR, None
    except FileNotFoundError:
        return EVIDENCE_UNREADABLE, None
    except OSError:
        return EVIDENCE_UNREADABLE, None
    opened = [anchor]
    try:
        segments = [one for one in reference.split("/") if one]
        if not segments:
            return EVIDENCE_NOT_REGULAR, None
        for segment in segments[:-1]:
            try:
                held = os.open(segment, directory_flags, dir_fd=opened[-1])
            except FileNotFoundError:
                return EVIDENCE_ABSENT, None
            except NotADirectoryError:
                # LINUX ANSWERS ENOTDIR, NOT ELOOP, for `O_DIRECTORY` on a
                # symlink to a directory. The open has ALREADY refused by this
                # point, so this `lstat` only decides which refusal to NAME --
                # it introduces no window, and an escape reported as "not a
                # directory" would send an operator looking for the wrong
                # thing.
                try:
                    if stat.S_ISLNK(os.lstat(segment,
                                             dir_fd=opened[-1]).st_mode):
                        return EVIDENCE_ESCAPES, None
                except OSError:
                    pass
                return EVIDENCE_NOT_REGULAR, None
            except OSError as failure:
                # ELOOP is the symlink refusal `O_NOFOLLOW` produces, and it is
                # the one that matters: an intermediate link, whether it was
                # always there or appeared a microsecond ago, cannot be walked
                # through.
                import errno

                if failure.errno in (errno.ELOOP, errno.EMLINK):
                    return EVIDENCE_ESCAPES, None
                return EVIDENCE_UNREADABLE, None
            opened.append(held)
        try:
            descriptor = os.open(segments[-1],
                                 os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
                                 | getattr(os, "O_NONBLOCK", 0),
                                 dir_fd=opened[-1])
        except FileNotFoundError:
            return EVIDENCE_ABSENT, None
        except IsADirectoryError:
            return EVIDENCE_NOT_REGULAR, None
        except OSError as failure:
            import errno

            if failure.errno == errno.ELOOP:
                return EVIDENCE_ESCAPES, None
            return EVIDENCE_UNREADABLE, None
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                os.close(descriptor)
                return EVIDENCE_NOT_REGULAR, None
        except OSError:
            os.close(descriptor)
            return EVIDENCE_UNREADABLE, None
        # THE ONE DESCRIPTOR THAT OUTLIVES THIS CALL. Its parents are closed
        # by the `finally` below and that cannot redirect it: what it refers
        # to was fixed when it was opened.
        return EVIDENCE_PRESENT, descriptor
    finally:
        for held in reversed(opened):
            try:
                os.close(held)
            except OSError:
                pass


def _say(value):
    print(json.dumps(value, indent=2, sort_keys=True))


def _refused(message):
    print("refused: " + message, file=sys.stderr)
    return 2


def _authority(taken, *, writable):
    """Open the named authority, read-only unless an act needs otherwise.

    READ-ONLY IS THE DEFAULT AND IS NOT A CONVENIENCE. Three of this command's
    five verbs only read, and a read verb that opened a store writably would
    take a write lock on a deployment somebody is serving from.
    """
    from baton_v12.authority import Authority

    if writable:
        return Authority.open(taken.authority_store,
                              expected_authority_uuid=taken.authority_uuid)
    return Authority.open_readonly(
        taken.authority_store, expected_authority_uuid=taken.authority_uuid)


def _instance(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


# -- the dossier verbs -------------------------------------------------------

def _bind(taken):
    with _authority(taken, writable=True) as authority:
        _say(authority.bind_dossier(taken.work, taken.locator,
                                    operation_id=taken.operation_id))
    return 0


def _read(taken):
    """Resolve an exact authority plus Work -- or a locator -- to one dossier.

    BOTH DIRECTIONS, because a human holding a directory name needs to get back
    to the authority as much as the other way round, and an absent binding is
    reported as `null` rather than as a failure: "this Work has no canonical
    record yet" is an answer.
    """
    with _authority(taken, writable=False) as authority:
        if taken.locator is not None:
            held = authority.dossier_work(taken.locator)
        else:
            held = authority.dossier_of(taken.work)
        _say({"authority_uuid": authority.authority_uuid, "dossier": held,
              "evidence": (authority.dossier_evidence(held["work_id"])
                           if held is not None else [])})
    return 0


def _cite(taken):
    """Digest one existing file and record it as this dossier's evidence.

    THE FILE IS READ HERE AND THE DIGEST IS WHAT CROSSES INTO THE AUTHORITY.
    The reference stays relative to `--root`, so the record stays portable
    across the hosts that will later resolve it.
    """
    from baton_v12.authority.dossier import check_evidence_reference

    # THE GRAMMAR BEFORE THE FILESYSTEM. Review P1: this read the path first,
    # so a malformed or escaping operand was opened and digested before the
    # authority was ever asked whether it was a citable reference at all.
    check_evidence_reference(taken.reference)
    state, digest, held = _contained_read(taken.root, taken.reference)
    if state != EVIDENCE_PRESENT:
        return _refused(
            f"{taken.reference!r} resolves under {taken.root!r} as "
            f"{state!r}, so there is nothing citable there; a dossier records "
            f"evidence that exists as a contained regular file, and bytes "
            f"reached through a symbolic link are not under this root")
    with _authority(taken, writable=True) as authority:
        said = authority.record_dossier_evidence(
            taken.work, taken.reference, digest,
            operation_id=taken.operation_id)
    _say(dict(said, bytes=held, root=os.path.abspath(taken.root)))
    return 0


def _verify(taken):
    """Every citation, resolved against a root, and an HONEST refusal otherwise.

    THREE OUTCOMES PER REFERENCE AND THEY ARE NOT THE SAME FACT. `present` is
    the digest matching. `absent` is the file not being there. `unreadable` is
    this process not being allowed to read it -- which is emphatically not
    "absent", because reporting a permission problem as a missing file sends an
    operator to restore something that was never lost. `changed` is the file
    being there and holding different bytes than the record cites.

    A DOSSIER WITH NO CITATIONS IS NOT VERIFIED. It is reported as
    `cited: 0` and refused: the acceptance asks for honest refusal when evidence
    is absent, and a record that cites nothing cannot be said to have intact
    evidence.
    """
    with _authority(taken, writable=False) as authority:
        held = authority.dossier_of(taken.work)
        if held is None:
            return _refused(
                f"Work {taken.work!r} has no canonical dossier in this "
                f"authority, so there is no evidence to verify")
        cited = authority.dossier_evidence(held["work_id"])
        # THE AUTHORITY'S OWN IDENTITY, asked of the authority rather than
        # sliced off a Work id, which merely LOOKS like a UUID.
        uuid = authority.authority_uuid
        # THE AUTHORITY'S OWN IDENTITY, asked of the authority. The first cut
        # reported `work_id[:8]`, which is the Work id's prefix and merely
        # LOOKS like a UUID -- a report naming the wrong authority is worse
        # than one naming none, because the whole acceptance is about an exact
        # authority plus Work resolving to one record.
        uuid = authority.authority_uuid
    findings = []
    for one in cited:
        state, actual, _held = _contained_read(taken.root, one["reference"])
        if state == EVIDENCE_PRESENT and actual != one["digest"]:
            state = "changed"
        findings.append({"reference": one["reference"], "state": state,
                         "cited_digest": one["digest"], "actual": actual})
    intact = [one for one in findings
              if one["state"] == EVIDENCE_PRESENT]
    answer = {"authority_uuid": uuid, "work_id": held["work_id"],
              "locator": held["locator"], "root": taken.root,
              "cited": len(findings), "intact": len(intact),
              "evidence": findings}
    _say(answer)
    if not findings:
        return _refused(
            f"dossier {held['locator']!r} cites no evidence, so its evidence "
            f"cannot be reported intact")
    if len(intact) != len(findings):
        return _refused(
            f"dossier {held['locator']!r} cites {len(findings)} pieces of "
            f"evidence and {len(findings) - len(intact)} did not resolve "
            f"intact under {taken.root!r}; the states above say which and why, "
            f"and nothing was changed")
    return 0


def _authority_schema_version():
    from baton_v12.authority.schema import SCHEMA_VERSION

    return SCHEMA_VERSION


def _store_member(path):
    """One store, its sidecar BYTES, and nothing taken on faith.

    THE SIDECARS ARE DIGESTED, not merely listed. The first cut recorded their
    NAMES, so a `-wal` holding committed transactions could be restored with
    different contents and every check still passed -- while the store's newest
    commits live in exactly those bytes.
    """
    held = {"path": path, "digest": _digest(path),
            "bytes": os.path.getsize(path), "sidecars": {}}
    for suffix in SIDECARS:
        beside = path + suffix
        if os.path.exists(beside):
            held["sidecars"][suffix] = {"digest": _digest(beside),
                                        "bytes": os.path.getsize(beside)}
    return held


def _tree_member(root):
    """A retained directory, bound by a CONTENT MANIFEST rather than copied.

    One digest over the sorted `path:digest` lines of every regular file under
    it, plus the count and the byte total. That binds the bytes without putting
    a deployment's whole retained output inside a manifest, and a later check
    recomputes the same three numbers.

    A SYMLINK IS RECORDED AS ONE AND NEVER FOLLOWED, so a retained tree cannot
    bind bytes that live somewhere else.
    """
    # REVIEW P1: `os.walk` WITHOUT AN ERROR HANDLER SILENTLY SKIPS a subtree
    # it cannot read, so an unreadable directory produced a smaller content
    # manifest and a clean claim. And a DIRECTORY symlink appears in
    # `directories`, never in `names`, so the previous comment about recording
    # links was false for exactly the entries that can leave the tree. Both are
    # recorded now, and either makes the walk incomplete rather than smaller.
    lines, count, total, links, unreadable = [], 0, 0, [], []
    for place, directories, names in os.walk(
            root, followlinks=False, onerror=lambda failure: unreadable.append(
                os.path.relpath(getattr(failure, "filename", root) or root,
                                root))):
        directories.sort()
        for name in sorted(directories):
            whole = os.path.join(place, name)
            if os.path.islink(whole):
                relative = os.path.relpath(whole, root)
                links.append(relative)
                lines.append(f"{relative}:dirlink:{os.readlink(whole)}")
        for name in sorted(names):
            whole = os.path.join(place, name)
            relative = os.path.relpath(whole, root)
            about = os.lstat(whole)
            if stat.S_ISLNK(about.st_mode):
                links.append(relative)
                lines.append(f"{relative}:symlink:{os.readlink(whole)}")
                continue
            if not stat.S_ISREG(about.st_mode):
                lines.append(f"{relative}:not-regular")
                continue
            lines.append(f"{relative}:{_digest(whole)}")
            count += 1
            total += about.st_size
    body = "\n".join(lines).encode("utf-8")
    return {"path": root, "files": count, "bytes": total,
            "symlinks": sorted(links), "unreadable": sorted(set(unreadable)),
            "content_digest": "sha256:" + hashlib.sha256(body).hexdigest()}


def _stored_identity(path, *, scratch=None):
    """The authority store's OWN recorded kind, version and UUID.

    THROUGH THE SUPPORTED OWNER SURFACE. Review 2026-10-18T08-48-00Z: the first
    cut ran raw `mode=ro` SQLite here, and including the `-shm` that read
    created in the manifest did not make the check read-only -- `_check` called
    it AFTER reporting the restored set unchanged, so a check could modify the
    set it had just certified. `Authority.stored_identity` is the authority's
    own read-only probe, the one `open` itself uses before it decides anything,
    exposed for exactly this question because `open` REFUSES a store this build
    does not speak and therefore cannot answer which version it is.

    AND WHEN A BYTE-IDENTICAL SET MUST SURVIVE, THE PROBE READS A COPY.
    `mode=ro` is SQLite's guarantee about the DATABASE; owner M128249 accepted
    that reading a WAL database may create or maintain its coordination files.
    So `scratch` copies the store and whatever sidecars are beside it, probes
    the copy, and leaves the restored set untouched -- which is a promise this
    program can keep rather than one it hoped SQLite would.
    """
    from baton_v12.authority import Authority

    held = path
    if scratch is not None:
        os.makedirs(scratch, exist_ok=True)
        held = os.path.join(scratch, os.path.basename(path))
        shutil.copyfile(path, held)
        for suffix in SIDECARS:
            if os.path.exists(path + suffix):
                shutil.copyfile(path + suffix, held + suffix)
    recorded = Authority.stored_identity(held)
    if recorded is None:
        return {"unreadable": "the file is not a database this build can read"}
    return {"store_kind": recorded.get("store_kind"),
            "schema_version": recorded.get("schema_version"),
            "authority_uuid": recorded.get("authority_uuid")}


def _manifest(taken):
    """One CLOSED and consistent recovery SET for a retained instance.

    WHAT THE FIRST CUT GOT WRONG, reproduced by review through this very
    command: it hashed three store files, copied the provenance as optional
    values it never validated, listed sidecar NAMES without their bytes, bound
    no retained inputs, outputs, contexts or workspaces, and emitted a document
    with `authority_uuid: null` and `provenance: {null, null, null}` while
    exiting 0. A manifest that cannot say which deployment it describes is not
    a recovery set.

    SO THE INSTANCE IS VALIDATED FIRST and the member set is CLOSED. Every
    required member must be present; a missing one refuses here rather than
    being carried into a document a later check would trust.

    IT IS STILL NOT A BACKUP AND TAKES NONE. It digests what is there now.
    Choosing a cut, stopping admissions and accounting for writers are operator
    acts, and Slawomir owns production backup and restore.
    """
    try:
        instance = _instance(taken.instance)
    except (OSError, ValueError) as failure:
        return _refused(f"{taken.instance!r} did not read as an instance "
                        f"document: {type(failure).__name__}: {failure}")
    # THE REAL VALIDATOR, not a hand-rolled subset. Review 2026-10-18T09-04-00Z
    # P1: this checked schema, UUID and destination itself and then looked for
    # an `authority_store` MEMBER -- which `tools.instance.emit` does not emit.
    # So a genuine instance refused and a handcrafted selector carrying an
    # invented member passed, which is producer/consumer disagreement dressed
    # as validation.
    
    wrong = instance_contract.malformed(instance, taken.instance)
    if wrong:
        return _refused(
            f"{taken.instance!r} is not a supported instance selector: "
            f"{wrong}. A recovery set is derived from the instance contract, "
            f"not from a document that merely resembles one")
    # AND THE STORES COME FROM THE LAYOUT, which is the contract's own answer
    # to where they live -- "derived, never configured twice". The authority
    # store has no selector member precisely because the layout owns it.
    places = instance_contract.layout(instance["destination"])
    declared = {"authority_store": places["authority_store"],
                "job_store": instance["job_store"],
                "control_store": instance["control_store"]}
    faults = []
    for name in ("job_store", "control_store"):
        if declared[name] != places[name]:
            faults.append(f"the selector's {name} is {declared[name]!r} and "
                          f"its destination derives {places[name]!r}")
    if faults:
        return _refused(
            f"{taken.instance!r} describes a different deployment than its own "
            f"destination: " + "; ".join(faults) + ". Every path an instance "
            f"owns is derived from that destination, so one that disagrees is "
            f"not this instance's recovery set")
    # THE STORE'S OWN IDENTITY IS READ FIRST, and the order is a correction
    # rather than a preference. A `mode=ro` connection to a WAL database
    # CREATES the shared-memory sidecar when the directory allows it -- W316915
    # measured exactly that -- so reading the identity after digesting the
    # members produced a manifest that did not record a sidecar its own read
    # had just made. A copy then carried that file, and `_check` correctly
    # reported it as a writer signal: this program making its own evidence
    # look tampered with. Reading first means whatever the read creates is
    # part of what the manifest describes.
    stored = None
    authority_place = declared["authority_store"]
    if os.path.isfile(authority_place):
        # ON A COPY HERE TOO. Review P1: only `_check` copied, so manifest
        # creation still ran the `mode=ro` probe against the original and the
        # comment beside it described creating an SHM before hashing it. Both
        # commands keep the source bytes now, and neither claims the other's
        # evidence.
        scratch = tempfile.mkdtemp(prefix="v12-recovery-probe-")
        try:
            stored = _stored_identity(authority_place, scratch=scratch)
        except Exception as failure:                         # noqa: BLE001
            stored = {"unreadable": f"{type(failure).__name__}: {failure}"}
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    members, missing = {}, []
    for name in STORES:
        path = declared[name]
        if not os.path.isfile(path):
            missing.append(name)
            continue
        members[name] = _store_member(path)
    # THE PROVENANCE IS BOUND BY VALUE. `deployment` is a document, so its
    # BYTES are digested; `identity` and `runtime` are structures the instance
    # records, so their canonical bytes are. The first cut copied all three as
    # values nothing checked, which is how a store could be restored beside a
    # different build and still be called compatible.
    provenance = {}
    for name in PROVENANCE:
        held = instance.get(name)
        if name == "deployment":
            if not isinstance(held, str) or not os.path.isfile(held):
                missing.append(name)
                continue
            provenance[name] = {"path": held, "digest": _digest(held),
                                "bytes": os.path.getsize(held)}
            continue
        if held is None:
            missing.append(name)
            continue
        body = json.dumps(held, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")
        provenance[name] = {
            "value": held,
            "digest": "sha256:" + hashlib.sha256(body).hexdigest()}
    # THE RETAINED EVIDENCE, bound by content manifest. Absent is recorded as
    # absent rather than skipped: a later check must be able to tell "this
    # deployment had no logs" from "nobody looked".
    # THE RETAINED INVENTORY IS REQUIRED, not best-effort. Review P1: an
    # omitted field and a missing configured directory were both treated as
    # "nothing was retained", so removing the whole axis passed. The INSTANCE
    # CONTRACT decides: a root it names must exist and be walkable, and a root
    # it does not name is the only legitimate absence.
    # THE CONTRACT'S OWN REQUIRED ROOTS. Review P1: `not-configured` was a
    # bypass -- removing state, logs and repository from a selector made the
    # manifest succeed and a restore with all three deleted pass, which is the
    # same false-completeness hole behind a new label. `instance._MEMBERS`
    # REQUIRES all three, so an absent one is a malformed selector (already
    # refused above) and never a legitimate absence here.
    retained = {}
    for name in RETAINED:
        place = places[name]
        if not os.path.isdir(place):
            retained[name] = {"path": place, "state": "absent"}
            missing.append(f"retained:{name}")
            continue
        walked = _tree_member(place)
        if walked["unreadable"]:
            retained[name] = dict(walked, state="unreadable")
            missing.append(f"retained:{name}")
            continue
        retained[name] = dict(walked, state="present")
    answer = {
        "schema": RECOVERY_SCHEMA,
        "instance": os.path.abspath(taken.instance),
        "instance_digest": _digest(taken.instance),
        # THE SELECTOR DOCUMENT ITSELF, not only its digest. `/3` adds this
        # because `recovery-check` cannot otherwise tell a RELOCATED selector
        # (destination rewritten to where the set actually landed, every other
        # member identical) from arbitrarily rewritten bytes. Without it the
        # only honest answer to a changed selector is to refuse every restore
        # that moved.
        "instance_document": instance,
        "destination": instance["destination"],
        "authority_uuid": instance["authority_uuid"],
        "required_members": list(STORES),
        "required_provenance": list(PROVENANCE),
        "required_retained": list(RETAINED),
        "members": members,
        "provenance": provenance,
        "retained": retained,
        "missing_members": sorted(missing),
        "stored_identity": stored,
        "not_a_backup": ("this manifest records what was present; taking the "
                         "cut, stopping admissions and accounting for writers "
                         "are operator acts, and Slawomir owns production "
                         "backup and restore"),
    }
    _say(answer)
    if missing:
        return _refused(
            "this instance is missing recovery-set members "
            + ", ".join(sorted(missing))
            + "; a partial set is not a recoverable deployment")
    held = answer["stored_identity"] or {}
    if held.get("store_kind") != AUTHORITY_STORE_KIND \
            or held.get("authority_uuid") != instance["authority_uuid"]:
        return _refused(
            f"the authority store's own metadata says kind "
            f"{held.get('store_kind')!r} and UUID "
            f"{held.get('authority_uuid')!r}, which is not this instance's "
            f"{AUTHORITY_STORE_KIND!r}/{instance['authority_uuid']!r}; a set "
            f"whose store is not the instance's own store is not its recovery "
            f"set")
    return 0


def _check(taken):
    """Is this restored set COMPLETE, UNCHANGED, THIS deployment's, and
    readable by this build -- and has anybody accounted for the old writer?

    WHAT REVIEW REPRODUCED. The first cut iterated whatever members the
    supplied manifest happened to contain, so a synthetic document naming one
    ordinary file as `authority_store` returned 0 with `faults: []` and
    `schema_compatible: true`. It ignored `missing_members`, never looked at the
    provenance, and compared the EMITTING BUILD's schema constant rather than
    the stored one. And without `--flat` it checked the recorded ABSOLUTE
    paths, so the required `--root` was ignored entirely.

    EVERY ONE OF THOSE IS A SEPARATE REFUSAL NOW:

      THE SET MUST BE CLOSED. Every required member and every required
      provenance entry must be in the manifest AND on disk under the restored
      root, at its recorded digest, with its sidecar bytes. A manifest that
      declared members missing is refused for that alone.

      IT MUST BE THIS DEPLOYMENT'S. The restored authority store's own `meta`
      says its kind, version and UUID; a store that is not the manifest's own
      store is not its recovery set however well its digest matches.

      COMPATIBILITY IS THE STORED VERSION'S. Read from the restored file, not
      from the constant this program was compiled with.

      THE ROOT IS ALWAYS HONOURED. Members resolve under `--root` -- preserving
      the recorded layout relative to the original destination by default, or
      side by side with `--flat`.

    AND IT NEVER ACCOUNTS FOR THE WRITER. Review P1 is explicit that a
    destination directory disappearing is not proof that an old runtime
    stopped, and the first cut treated exactly that as the accounting. So this
    reports uncertainty SIGNALS and never clears the obligation: a clean report
    means these checks found no fault, and positively accounting for every
    runtime and launch of the previous instance remains the operator's act.
    """
    try:
        with open(taken.manifest, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
    except (OSError, ValueError) as failure:
        return _refused(f"{taken.manifest!r} did not read as a recovery set: "
                        f"{type(failure).__name__}: {failure}")
    if not isinstance(manifest, dict) \
            or manifest.get("schema") != RECOVERY_SCHEMA:
        return _refused(
            f"{taken.manifest!r} is not a {RECOVERY_SCHEMA} document")
    faults, writers = [], []
    required = list(manifest.get("required_members") or STORES)
    if sorted(required) != sorted(STORES):
        faults.append(f"the manifest declares required members {required} "
                      f"rather than this build's closed set {list(STORES)}")
    declared_missing = manifest.get("missing_members") or []
    if declared_missing:
        faults.append(f"the manifest itself records missing members "
                      f"{sorted(declared_missing)}, so it never described a "
                      f"complete deployment")
    destination = manifest.get("destination")
    if not isinstance(destination, str) or not destination:
        faults.append("the manifest names no original destination, so its "
                      "members cannot be resolved under a restored root")
        destination = None

    def restored(path):
        """Where this member should be found under the selected root."""
        if taken.flat:
            return os.path.join(taken.root, os.path.basename(path))
        if destination and (path == destination
                            or path.startswith(destination.rstrip("/") + "/")):
            return os.path.join(taken.root,
                                os.path.relpath(path, destination))
        return None

    # THE RESTORED SELECTOR IS A REQUIRED MEMBER AND IS BOUND BY ITS BYTES.
    # Review 2026-10-18T09-12-00Z reproduced both halves of this: the selector
    # was read only if it happened to exist, so deleting it added no fault, and
    # its recorded `instance_digest` was never compared, so a structurally
    # valid selector naming ANOTHER authority UUID returned faults=[] and
    # schema_compatible=true. A set whose own instance document is missing, or
    # is a different document, is not a restorable deployment.
    #
    # EXACTLY ONE REWRITE IS SUPPORTED, and it is named rather than tolerated:
    # a RELOCATED selector whose `destination` is the root the set actually
    # landed under, with every other member byte-identical to the recorded
    # document. Anything else is `changed`, including a relocation to some
    # third path that is not this restore's own root.
    restored_places, restored_selector = None, None
    recorded_selector = manifest.get("instance_document")
    if not isinstance(recorded_selector, dict):
        faults.append("restored-instance-selector")
        restored_selector = {
            "state": "not-in-manifest",
            "why": f"a {RECOVERY_SCHEMA} manifest carries the selector "
                   f"document it cut, and this one does not, so a relocated "
                   f"selector could not be told from a rewritten one"}
    else:
        selector = restored(manifest.get("instance") or "")
        # PARSE SUCCESS AND THE PARSED VALUE ARE TWO FACTS. Review
        # 2026-10-18T09-29-00Z P2: `held_selector` carried both, and a file
        # holding a valid JSON `null` parses to None -- so the guard below
        # skipped the contract validator, left the state at `present`, and the
        # success branch indexed None and raised TypeError out of the public
        # command. `read` says whether JSON came back; the value says what.
        state, held_selector, why, read = "present", None, None, False
        if not selector or not os.path.isfile(selector):
            state = "absent"
        else:
            try:
                with open(selector, "r", encoding="utf-8") as handle:
                    held_selector = json.load(handle)
            except (OSError, ValueError) as failure:
                state, why = "unreadable", type(failure).__name__
            else:
                read = True
        if read:
            # EVERY PARSED VALUE GOES THROUGH THE REAL VALIDATOR, including
            # `null`, `[]`, a bare string and a number -- and the validator
            # already answers for all of them ("an instance selector is one
            # document, not NoneType"). Measured this claim rather than
            # assumed. A local isinstance check here would be a SECOND
            # definition of what a selector is, which is the thing that put a
            # handcrafted selector in this fixture two reviews ago.
            wrong = instance_contract.malformed(held_selector, selector)
            # WHERE THE SET ACTUALLY LANDED. The manifest's `destination`
            # maps to the selected root by construction, under `--flat` and
            # without it alike, so this is the one legal rewritten value.
            moved = os.path.abspath(taken.root)
            if wrong:
                state, why = "malformed", wrong
            elif held_selector.get("authority_uuid") \
                    != manifest.get("authority_uuid"):
                # The loudest version of this fault: intact, valid bytes that
                # describe somebody else's deployment.
                state = "another-authority"
                why = (f"the restored selector names authority "
                       f"{held_selector.get('authority_uuid')!r}, not this "
                       f"set's {manifest.get('authority_uuid')!r}")
            elif held_selector == recorded_selector:
                state = "present"
            elif os.path.abspath(held_selector.get("destination") or "") \
                    == moved \
                    and held_selector == dict(recorded_selector,
                                              destination=held_selector[
                                                  "destination"]):
                # The one supported transformation, and only to THIS root.
                state = "relocated"
            else:
                state = "changed"
                why = sorted(
                    set(held_selector) ^ set(recorded_selector)
                    or [member for member in recorded_selector
                        if held_selector.get(member)
                        != recorded_selector.get(member)])
        restored_selector = {"state": state, "path": selector,
                             "recorded_digest": manifest.get("instance_digest")}
        if why is not None:
            restored_selector["why"] = why
        if state in ("present", "relocated"):
            restored_selector["destination"] = held_selector["destination"]
            restored_places = instance_contract.layout(taken.root)
        else:
            faults.append("restored-instance-selector")
    held = manifest.get("members") or {}
    findings = {}
    for name in STORES:
        recorded = held.get(name)
        if not isinstance(recorded, dict):
            faults.append(name)
            findings[name] = {"state": "not-in-manifest"}
            continue
        whole = restored(recorded.get("path") or "")
        if whole is None:
            faults.append(name)
            findings[name] = {"state": "unresolvable",
                              "why": "the recorded path is not under the "
                                     "manifest's own destination"}
            continue
        state, actual = "present", None
        if not os.path.isfile(whole):
            state = "absent"
        else:
            try:
                actual = _digest(whole)
            except OSError as failure:
                state, actual = "unreadable", type(failure).__name__
            else:
                if actual != recorded.get("digest"):
                    state = "changed"
        sidecars = {}
        for suffix, about in sorted(
                (recorded.get("sidecars") or {}).items()):
            beside = whole + suffix
            if not os.path.isfile(beside):
                sidecars[suffix] = "absent"
                state = state if state != "present" else "sidecar-absent"
            elif _digest(beside) != about.get("digest"):
                sidecars[suffix] = "changed"
                state = state if state != "present" else "sidecar-changed"
            else:
                sidecars[suffix] = "present"
        # A SIDECAR THAT APPEARED is a writer question, not a digest fault.
        for suffix in SIDECARS:
            if suffix not in (recorded.get("sidecars") or {}) \
                    and os.path.exists(whole + suffix):
                writers.append(f"{name} has a {suffix} the manifest did not "
                               f"record, so something opened this store since "
                               f"the cut")
        findings[name] = {"path": whole, "state": state,
                          "recorded_digest": recorded.get("digest"),
                          "actual": actual, "sidecars": sidecars}
        if state != "present":
            faults.append(name)
    provenance = {}
    for name in PROVENANCE:
        recorded = (manifest.get("provenance") or {}).get(name)
        if not isinstance(recorded, dict) or not recorded.get("digest"):
            faults.append(f"provenance:{name}")
            provenance[name] = {"state": "not-in-manifest"}
            continue
        if "path" not in recorded:
            # A recorded STRUCTURE: its canonical bytes are the evidence and
            # they travel inside the manifest, so this verifies the binding.
            body = json.dumps(recorded.get("value"), sort_keys=True,
                              separators=(",", ":")).encode("utf-8")
            actual = "sha256:" + hashlib.sha256(body).hexdigest()
            state = ("present" if actual == recorded["digest"]
                     else "changed")
            provenance[name] = {"state": state, "actual": actual,
                                "recorded_digest": recorded["digest"]}
            if state != "present":
                faults.append(f"provenance:{name}")
            continue
        whole = restored(recorded["path"])
        if whole is None or not os.path.isfile(whole):
            provenance[name] = {"state": "absent", "path": whole}
            faults.append(f"provenance:{name}")
            continue
        actual = _digest(whole)
        state = "present" if actual == recorded["digest"] else "changed"
        provenance[name] = {"state": state, "path": whole, "actual": actual,
                            "recorded_digest": recorded["digest"]}
        if state != "present":
            faults.append(f"provenance:{name}")
    # THE CLOSED RETAINED INVENTORY, which review P1 found iterated rather
    # than required: deleting the whole `retained` field from a manifest and
    # every restored tree with it returned 0 with a clean report.
    declared_retained = list(manifest.get("required_retained") or [])
    if sorted(declared_retained) != sorted(RETAINED):
        faults.append(f"the manifest declares required retained roots "
                      f"{declared_retained} rather than this build's closed "
                      f"set {list(RETAINED)}")
    retained = {}
    for name in RETAINED:
        recorded = (manifest.get("retained") or {}).get(name)
        if not isinstance(recorded, dict):
            retained[name] = {"state": "not-in-manifest"}
            faults.append(f"retained:{name}")
            continue
        if recorded.get("state") == "not-configured":
            # NO LONGER A LEGITIMATE ANSWER. The instance contract REQUIRES
            # state, logs and repository, so a manifest claiming one was never
            # configured describes a selector the real validator rejects --
            # review P1 showed that label letting a restore with all three
            # deleted pass clean.
            retained[name] = {"state": "not-configured-but-required"}
            faults.append(f"retained:{name}")
            continue
        if recorded.get("state") != "present":
            retained[name] = {"state": "incomplete-at-cut",
                              "recorded": recorded.get("state")}
            faults.append(f"retained:{name}")
            continue
        whole = restored(recorded.get("path") or "")
        if whole is None or not os.path.isdir(whole):
            retained[name] = {"state": "absent", "path": whole}
            faults.append(f"retained:{name}")
            continue
        # AND THE RESTORED BINDING IS VERIFIED, not assumed: the restored tree
        # must be where the restored instance's own destination derives it.
        if restored_places is not None \
                and restored_places.get(name) not in (None, whole):
            faults.append(f"retained:{name}")
            retained[name] = {"state": "not-at-its-derived-path",
                              "path": whole,
                              "derived": restored_places.get(name)}
            continue
        actual = _tree_member(whole)
        same = (not actual["unreadable"]
                and actual["content_digest"] == recorded.get("content_digest")
                and actual["files"] == recorded.get("files")
                and actual["bytes"] == recorded.get("bytes"))
        retained[name] = {
            "state": ("present" if same
                      else "unreadable" if actual["unreadable"] else "changed"),
            "path": whole, "files": actual["files"], "bytes": actual["bytes"],
            "unreadable": actual["unreadable"],
            "content_digest": actual["content_digest"],
            "recorded_digest": recorded.get("content_digest")}
        if not same:
            faults.append(f"retained:{name}")
    # IDENTITY AND COMPATIBILITY FROM THE RESTORED STORE ITSELF.
    recorded_identity = manifest.get("stored_identity") or {}
    stored, compatible = None, False
    authority_place = findings.get("authority_store", {}).get("path")
    if authority_place and os.path.isfile(authority_place):
        # ON A COPY. Review P1: this ran after the digests were reported, so a
        # `mode=ro` probe creating a `-shm` would modify the very set this
        # command had just called unchanged. The copy makes the promise
        # keepable, and `unchanged_after` below PROVES it rather than asserting
        # it.
        scratch = tempfile.mkdtemp(prefix="v12-recovery-probe-")
        try:
            stored = _stored_identity(authority_place, scratch=scratch)
        except Exception as failure:                         # noqa: BLE001
            stored = {"unreadable": f"{type(failure).__name__}: {failure}"}
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
    if not isinstance(stored, dict) or stored.get("store_kind") is None:
        faults.append("stored-identity")
    else:
        if stored.get("store_kind") != AUTHORITY_STORE_KIND:
            faults.append("stored-identity")
        if stored.get("authority_uuid") != manifest.get("authority_uuid"):
            faults.append("stored-identity")
        if recorded_identity.get("schema_version") is not None \
                and stored.get("schema_version") \
                != recorded_identity.get("schema_version"):
            faults.append("stored-identity")
        compatible = stored.get("schema_version") == str(
            _authority_schema_version())
    if destination and os.path.exists(destination):
        writers.append(
            f"the original instance destination {destination!r} still exists, "
            f"so the deployment that wrote these bytes has not been "
            f"positively accounted for")
    # AND THE SET IS RE-READ AFTER EVERY OBSERVATION, so "unchanged" is a
    # measurement rather than a hope. Review P1 is explicit that a check must
    # preserve byte and sidecar identity on success AND on refusal.
    unchanged_after = {}
    for name in STORES:
        whole = findings.get(name, {}).get("path")
        if not whole or not os.path.isfile(whole):
            continue
        recorded = (manifest.get("members") or {}).get(name) or {}
        beside = sorted(one for one in SIDECARS
                        if os.path.exists(whole + one))
        same = _digest(whole) == recorded.get("digest")
        unchanged_after[name] = {
            "digest_unchanged": same,
            "sidecars_now": beside,
            "sidecars_at_cut": sorted(recorded.get("sidecars") or {})}
        if not same:
            faults.append(f"{name} changed while this check was running")
        if beside != sorted(recorded.get("sidecars") or {}):
            writers.append(f"{name} gained or lost a sidecar while this check "
                           f"was running")
    answer = {"manifest": os.path.abspath(taken.manifest), "root": taken.root,
              "layout": "flat" if taken.flat else "as-recorded",
              "unchanged_after_observation": unchanged_after,
              "restored_selector": restored_selector,
              "members": findings, "provenance": provenance,
              "retained": retained,
              "faults": sorted(set(faults)),
              "writer_uncertainty": writers,
              "stored_identity": stored,
              "build_speaks_schema_version": _authority_schema_version(),
              "schema_compatible": compatible,
              "operator_must_account_for_writers": True,
              "writable_admission": "refused"}
    if answer["faults"] or writers or not compatible:
        _say(answer)
        why = []
        if answer["faults"]:
            why.append("recovery-set portions " + ", ".join(answer["faults"])
                       + " are missing, unreadable, changed or not this "
                         "deployment's")
        if writers:
            why.append("an earlier writer cannot be ruled out")
        if not compatible:
            why.append(
                f"the restored authority store records schema "
                f"{(stored or {}).get('schema_version')!r} and this build "
                f"speaks {_authority_schema_version()}, and this authority "
                f"does not migrate in either direction")
        return _refused(
            "; ".join(why) + ". No writable admission is possible, nothing "
            "was changed, and no hold was cleared")
    # NOT AN ADMISSION, AND NOT A CESSATION FINDING. Review P1: fixture or
    # destination deletion is not proof that a runtime stopped, so this says
    # what these checks did and leaves the accounting where it belongs.
    answer["writable_admission"] = (
        "these checks found no fault in the restored set. They do NOT "
        "establish that the previous instance stopped: admitting this set "
        "writably requires the operator to positively account for every "
        "runtime and launch of it, and no absence of a directory proves that")
    _say(answer)
    return 0


VERBS = {"bind": _bind, "read": _read, "cite": _cite, "verify": _verify,
         "recovery-manifest": _manifest, "recovery-check": _check}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(
        prog="baton-v12-stack record",
        description="The canonical dossier binding and the retained-instance "
                    "recovery set. Reads are read-only; nothing here migrates, "
                    "copies or restores a live instance.")
    verbs = parser.add_subparsers(dest="verb", required=True)

    def store_operands(one, *, uuid=True):
        one.add_argument("--authority-store", required=True)
        if uuid:
            one.add_argument("--authority-uuid", required=True)

    bind = verbs.add_parser("bind", help="bind one Work to one flat dossier")
    store_operands(bind)
    bind.add_argument("--work", required=True)
    bind.add_argument("--locator", required=True)
    bind.add_argument("--operation-id", required=True)

    read = verbs.add_parser("read", help="resolve a Work or a locator")
    store_operands(read)
    read.add_argument("--work")
    read.add_argument("--locator")

    cite = verbs.add_parser("cite", help="digest a file and cite it")
    store_operands(cite)
    cite.add_argument("--work", required=True)
    cite.add_argument("--root", required=True)
    cite.add_argument("--reference", required=True)
    cite.add_argument("--operation-id", required=True)

    verify = verbs.add_parser("verify", help="resolve every citation")
    store_operands(verify)
    verify.add_argument("--work", required=True)
    verify.add_argument("--root", required=True)

    manifest = verbs.add_parser("recovery-manifest",
                                help="the recovery set of a retained instance")
    manifest.add_argument("--instance", required=True)

    check = verbs.add_parser("recovery-check",
                             help="is a restored set complete and unclaimed")
    check.add_argument("--manifest", required=True)
    check.add_argument("--root", required=True)
    check.add_argument("--flat", action="store_true",
                       help="members were restored side by side under --root "
                            "rather than at their recorded absolute paths")

    taken = parser.parse_args(argv)
    if taken.verb == "read" and (taken.work is None) == (taken.locator is None):
        return _refused("read names exactly one of --work or --locator")
    from baton_v12.authority.errors import Refusal

    try:
        return VERBS[taken.verb](taken)
    except Refusal as refusal:
        # THE AUTHORITY'S OWN SENTENCE, not a traceback. Every refusal this
        # command can reach is a contract answer an operator is meant to read.
        return _refused(str(refusal))
    except OSError as failure:
        return _refused(f"{type(failure).__name__}: {failure}")


if __name__ == "__main__":                                  # pragma: no cover
    raise SystemExit(main())
