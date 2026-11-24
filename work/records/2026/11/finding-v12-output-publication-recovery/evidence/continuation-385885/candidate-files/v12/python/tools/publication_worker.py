"""THE HOST SIDE OF ONE DETERMINISTIC PUBLICATION: the adapter that adopts
the staged bytes, and the seam a deployment composes it into.

W385695 internal checkpoint 2, under DESIGN REC-9 and the owner-selected
contract `work/records/2026/11/finding-v12-output-publication-recovery/
CONTRACT-PROPOSED-385720.md`.

WHY IT IS HERE AND NOT IN THE PRODUCT PACKAGE. `tools/recovery_execution`
records the split and it is the same one: `baton_v12` owns every RULE about
what may be published, from which bytes, under which declaration and inside
which bound, and takes the act itself as an injected port. Writing files into
an execution's own output root is a host act, so this module is that port and
the configuration around it, and it decides nothing:

    PublicationWriter    adopts measured bytes and publishes an envelope
    PublicationSeam      the eight members `check_publication_seam` proves
    publication_seam()   composes them over one instance's own layout
    staging_root()       the private root recovery-owned staging lives under

WHAT THIS WRITER WILL NOT DO, and each is a refusal rather than a convention:

  * NO PROVIDER AND NO MODEL. There is no provider client here, no credential
    slot, no session and nothing that could hold one. Its answer declares
    `provider_invocations: 0` and the manager REFUSES any other number -- so
    the count is a checked fact rather than a claim about this file.
  * NO COMMAND AT ALL. It imports no `subprocess`, runs no verifier and has
    no argv operand to run one with. `verifier_invocations` is 0 for the same
    reason and is checked the same way.
  * NO BYTES OF ITS OWN IN THE PROPOSAL. The adopted tree is produced by ONE
    no-follow copy-and-measure pass out of the staged original, and the
    recovery's provenance goes to its own SEPARATE declared path. This writer
    cannot add a file to the proposal because it never opens one for writing
    inside it.
  * NO UNBOUNDED WORK. The manager hands it the ABSOLUTE deadline and the
    seconds remaining of it, and the bound is re-checked before each of the
    three things it does. A bound that elapses mid-adoption stops the work and
    answers `unknown` with `timed_out` beside it -- which can never read as a
    publication, because `published` is the only outcome the manager accepts.
  * NO SECOND TURN AND NO RETRY. It is called once per recovery by a
    journalled operation whose intent is durable before the call; it holds no
    retry of its own, which is what the approved profile's zero retries and
    zero continuations mean on this side of the boundary.

WHY THE COMPLETION ENVELOPE IS COMPOSED HERE. `v12/worker/baton_worker.py`
publishes it for a CONTAINER worker, from the container's own fixed `/output`,
and it is not importable from the manager distribution. This is a different
worker -- the deterministic publication worker, which runs no agent -- so it
composes its own and then puts it through `contracts.check_manifest_structure`,
the one shipped validator the manager's own freeze uses. The composition is
eight fields; the RULES are the shipped ones, and a drift between the two
documents is a failing validation rather than a quiet disagreement.
"""

import json
import os
import sys
from datetime import datetime

from baton_v12.contracts import (ContractRefusal, canonical_bytes,
                                 check_manifest_structure, digest)
from baton_v12.job_manager import publication_recovery
from baton_v12.worker_manager.workspaces import copied_manifest

__all__ = ["PublicationWriter", "PublicationSeam", "COMPLETION_SCHEMA",
           "COMPLETION_MANIFEST", "DEFAULT_STAGING", "DISPOSITION",
           "METADATA_KEY",
           "publication_seam", "staging_root", "main"]

# WHERE A DEPLOYMENT ALLOCATES PRIVATE RECOVERY STAGING, under its own state
# root. A sibling of the stores rather than a child of custody, which is
# `recovery_execution.DEFAULT_WORKSPACES`' reason: a writable tree inside the
# immutable evidence it is a copy of is a wider boundary than the contract
# declares. And the contract's own sentence, kept by the location: "private
# staging is not custody".
DEFAULT_STAGING = "publication-staging"
PRIVATE = 0o700

# THE WORKER CONTRACT'S OWN NAMES, spelled once. `COMPLETION_MANIFEST` is the
# name the manager's freeze reads and `COMPLETION_SCHEMA` is what it validates
# the document as; both are the frozen worker contract's and neither is this
# module's choice.
COMPLETION_MANIFEST = "output.json"
COMPLETION_SCHEMA = "baton.worker-manifest/completion"
DISPOSITION = "completed"
PRESENT = "present"
# WHERE THIS WORKER'S OWN ACCOUNT OF AN OUTPUT GOES inside the envelope's
# per-output metadata. `extensions` admits only namespaced keys, which is the
# frozen contract's way of keeping one worker's notes from colliding with
# another's; a bare member name is not an extension.
METADATA_KEY = "baton.v12.output-publication/1"


def _refuse(message, *, category="refused", code="precondition"):
    raise ContractRefusal(category, code, message)


def _instant(value):
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:                                    # pragma: no cover
        return None


class PublicationWriter:
    """ONE deterministic adoption, and an account of exactly what it did.

    IT ANSWERS FACTS AND NEVER A JUDGEMENT, `recovery_execution.CommandRunner`'s
    rule: `outcome` is whether it finished, the two counts are what it
    invoked, the manifests are what it measured and the instants are when. It
    returns no verdict word about whether the publication is the approved one
    -- that is the manager's own measurement, which is why nothing here
    compares a digest to the owner's decision.
    """

    def __init__(self, identity, *, clock, workspace_of):
        self._identity = identity
        self._clock = clock
        # WHERE THIS ATTEMPT'S OUTPUT ROOT IS, resolved by the OWNER that
        # prepared it and handed in as a callable. A path operand would make a
        # caller able to point this writer at a tree the manager never
        # prepared, which is the transport the whole workspace boundary exists
        # to retire.
        self._workspace_of = workspace_of

    def instance(self):
        return self._identity

    def adopt(self, request):
        """Adopt the staged bytes into this attempt's declared outputs.

        THE THREE THINGS IT DOES, in the order the contract fixes and with the
        bound re-checked before each:

          the PROPOSAL, by one no-follow copy-and-measure pass out of the
            read-only staged original into the declared candidate path;
          the PROVENANCE, the same way, into its own SEPARATE declared path;
          the COMPLETION ENVELOPE, composed over what was actually measured,
            validated by the shipped validator and published ATOMICALLY last
            -- because its presence under its final name IS the completion
            signal, so it must exist only once everything it describes is
            written.
        """
        taken = self._owned(request)
        started = self._clock()
        deadline = taken["deadline"]
        written = {}
        for name, source, declaration in (
                ("candidate", taken["staged"]["locator"],
                 taken["outputs"]["candidate"]),
                ("provenance", taken["provenance"]["locator"],
                 taken["outputs"]["provenance"])):
            left = self._remaining(deadline)
            if left is not None and left <= 0:
                return self._stopped(taken, started, at=name)
            into = os.path.join(self._place(taken), declaration["path"])
            if os.path.lexists(into):
                _refuse(f"the publication attempt's output already carries "
                        f"{declaration['path']!r}; an adoption writes its "
                        f"declared outputs once and never over an "
                        f"interrupted pass's bytes",
                        category="integrity", code="path")
            os.makedirs(into, mode=0o700)
            written[name] = copied_manifest(
                _place_of(source), into,
                max_entries=declaration["constraints"]["max_entries"],
                max_bytes=declaration["constraints"]["max_bytes"])
        left = self._remaining(deadline)
        if left is not None and left <= 0:
            return self._stopped(taken, started, at="envelope")
        envelope = self._envelope(taken, written)
        return {"outcome": "published",
                "provider_invocations": 0, "verifier_invocations": 0,
                "started_at": started, "ended_at": self._clock(),
                "manifest": written["candidate"],
                "provenance": written["provenance"],
                "envelope": envelope, "timed_out": False}

    # -- the operands this writer is given -----------------------------------

    def _owned(self, request):
        """The manager's own adoption request, proved before anything is
        written.

        IT IS THE MANAGER'S DOCUMENT AND IT IS STILL CHECKED, for
        `boundaries.adopted`'s reason: the member set is what this adapter
        decides with, and an adapter that discovered a missing one halfway
        through would have copied a proposal and then been unable to publish
        an envelope describing it.
        """
        if type(request) is not dict:
            _refuse("an adoption request is one closed object",
                    category="integrity", code="schema")
        for member in ("attempt_id", "assignment", "staged", "provenance",
                       "outputs", "deadline"):
            if member not in request:
                _refuse(f"an adoption request carries {member}",
                        category="integrity", code="schema")
        for forbidden in ("argv", "command", "environment", "credentials",
                          "provider", "task"):
            if forbidden in request:
                raise ContractRefusal(
                    "policy", "denied",
                    f"an adoption request carries {forbidden!r}; a "
                    f"deterministic publication runs no command, holds no "
                    f"credential and invokes no provider, and a request that "
                    f"named one would be asking this writer to be a different "
                    f"worker")
        return request

    def _place(self, taken):
        place = self._workspace_of(taken["attempt_id"])
        if not os.path.isdir(place) or os.path.islink(place):
            _refuse(f"the publication attempt's output root {place!r} is not "
                    f"a directory this writer may adopt into",
                    category="integrity", code="path")
        return place

    def _remaining(self, deadline):
        """THE SECONDS LEFT OF THE ABSOLUTE BOUND, recomputed every time.

        FROM THE INSTANT AND NOT FROM THE NUMBER THE MANAGER PASSED. The
        manager's `remaining_seconds` was true when it composed the request;
        what this writer must stop at is the absolute instant, so the
        remainder is derived again against this host's own clock on every
        check. A writer that counted down from the number it was handed would
        be running a worker-local timer, which is the one thing this bound
        must never be.
        """
        at = deadline.get("deadline_at")
        if at is None:
            return None
        wall, now = _instant(at), _instant(self._clock())
        if wall is None or now is None:                   # pragma: no cover
            return None
        return int((wall - now).total_seconds())

    def _stopped(self, taken, started, *, at):
        """THE BOUND ENDED IT, and that is reported as its own fact.

        `unknown` RATHER THAN A FAILURE, and never `published`: what this
        writer can say is that it stopped, not that the attempt produced
        nothing -- bytes it had already copied are still there, and the
        manager's own measurement is what decides whether anything usable
        exists. `timed_out` beside it is why. A ceiling having stopped the
        work can therefore never read as a passed publication.
        """
        return {"outcome": "unknown",
                "provider_invocations": 0, "verifier_invocations": 0,
                "started_at": started, "ended_at": self._clock(),
                "timed_out": True,
                "detail": f"the absolute publication bound "
                          f"{taken['deadline'].get('deadline_at')} was "
                          f"reached before this writer finished {at}"}

    # -- the completion envelope ---------------------------------------------

    def _envelope(self, taken, written):
        """`<workspace>/output.json`, published LAST and ATOMICALLY.

        LAST, because its presence under its final name is the completion
        signal: it exists only if everything it describes was already written,
        so no separate signal is needed and none is invented. ATOMICALLY,
        because writing bytes into the final name is not publication -- a
        process stopped inside that write leaves the name existing and
        incomplete, and the manager cannot tell that from a settled answer.

        VALIDATED BY THE SHIPPED VALIDATOR BEFORE IT IS WRITTEN. The manager's
        freeze puts this document through `check_manifest_structure` and
        refuses one it cannot read; composing a document that would fail there
        and discovering it at the freeze would be discovering it with an
        execution already over.
        """
        outputs = []
        for name, declaration in sorted(taken["outputs"].items()):
            measured = written[name]
            outputs.append({
                "name": declaration["name"], "type": declaration["type"],
                "path": declaration["path"], "status": PRESENT,
                "content_manifest": {
                    "entries": [dict(one) for one in measured["entries"]],
                    "entry_count": measured["entry_count"],
                    "total_bytes": measured["total_bytes"],
                    "tree_digest": measured["tree_digest"]},
                # THE ONE EXTENSION KEY, in the namespaced grammar
                # `extensions` keeps. A bare member name is not an extension
                # and the frozen schema says so; a document composed with one
                # would be refused by the validator below -- which is exactly
                # why the composition is validated before it is written.
                "result_metadata": {METADATA_KEY: {
                    "published_by": "deterministic publication worker",
                    "provider_invocations": 0,
                    "verifier_invocations": 0,
                    "adopted_from": "the approved retained original, "
                                    "delivered read-only"}}})
        body = {"version": {"major": 1, "minor": 0},
                "manifest_id": f"completion-{DISPOSITION}",
                "created_at": self._clock(),
                "extensions": {},
                "schema": COMPLETION_SCHEMA,
                "assignment_ref": taken["assignment"],
                "disposition": DISPOSITION,
                "outputs": sorted(outputs, key=lambda one: one["name"])}
        body["manifest_digest"] = digest(body)
        check_manifest_structure(body, "completionManifest",
                                 what="this publication's completion envelope")
        place = os.path.join(self._place(taken), COMPLETION_MANIFEST)
        staged = place + ".publishing"
        handle = os.open(staged,
                         os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600)
        try:
            os.write(handle, canonical_bytes(body))
            os.fsync(handle)
        finally:
            os.close(handle)
        os.replace(staged, place)
        return {"manifest_digest": body["manifest_digest"],
                "disposition": DISPOSITION, "created_at": body["created_at"]}


def _place_of(locator):
    """A `file://` locator this manager composed, as the path it names."""
    if not str(locator).startswith("file://"):
        _refuse(f"a staged locator is a file:// locator; this is {locator!r}",
                category="integrity", code="path")
    return str(locator)[len("file://"):]


class PublicationSeam:
    """The eight members `check_publication_seam` proves, as one object.

    IT CARRIES CONFIGURATION AND ONE CAPABILITY, exactly as
    `recovery_execution.VerificationSeam` does: the control store the attempt
    and its custody live in, the host owner of the original, the host's
    cessation evidence, the private staging root, the deterministic writer,
    and the Authority port and engine adapter the custody acts reach the host
    through.

    IT DECIDES NOTHING. Whether an original may be staged, whether a
    publication is the approved bytes, whether custody is attributable and
    whether review may be released are all the Job manager's, derived from
    durable state.
    """

    def __init__(self, *, control, host, exclusion, workspaces, writer,
                 authority, adapter):
        self.control = control
        self.host = host
        self.exclusion = exclusion
        self.workspaces = workspaces
        self.writer = writer
        self.authority = authority
        self.adapter = adapter


def staging_root(instance_root):
    """The private staging root of one instance, created if absent.

    0700 BECAUSE THIS MANAGER IS THE ONLY WRITER. The staged original is
    delivered READ-ONLY to one execution, and a group-writable scratch tree
    beside an approved original is a wider boundary than the one the contract
    declares.
    """
    place = os.path.join(os.path.realpath(str(instance_root)),
                         DEFAULT_STAGING)
    os.makedirs(place, mode=PRIVATE, exist_ok=True)
    os.chmod(place, PRIVATE)
    return place


def publication_seam(request):
    """Compose this deployment's publication seam over its own instance.

    THE DEFAULT FACTORY, in the shape `recovery_execution.verification_seam`
    already takes: which owners a pass acts through is a DEPLOYMENT fact, and
    the instance's own layout says which stores and which roots it owns.
    Nothing is searched for and nothing is guessed.
    """
    from tools.fresh_attempt_ports import instance_identity

    identity = instance_identity(request["instance"])
    return PublicationSeam(
        control=request["control_handle"],
        host=request["host"],
        exclusion=request["exclusion"],
        workspaces=staging_root(identity["root"]),
        writer=PublicationWriter(identity, clock=request["clock"],
                                 workspace_of=request["workspace_of"]),
        authority=request["authority"],
        adapter=request["adapter"])


def main(argv=None):                                      # pragma: no cover
    """Print the approved publication declarations, for an operator to read.

    THE ONE READ THIS MODULE OFFERS AN OPERATOR, and it is a read: the two
    declared outputs a recovery publishes under, with the owner-selected
    ceilings and the provenance descriptor's own bound. It records nothing,
    stages nothing and publishes nothing.
    """
    taken = list(sys.argv[1:] if argv is None else argv)
    if taken:
        raise SystemExit("usage: publication_worker")
    declaration = publication_recovery.corrective_declaration()
    json.dump({"candidate": declaration["output"],
               "declaration": declaration["descriptor"],
               "declaration_digest": declaration["digest"],
               "provenance": publication_recovery.PROVENANCE_OUTPUT},
              sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":                                # pragma: no cover
    raise SystemExit(main())
