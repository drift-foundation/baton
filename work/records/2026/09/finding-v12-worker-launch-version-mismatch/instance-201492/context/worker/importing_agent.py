"""The deterministic fixture INTEGRATOR: an approved bundle, imported exactly.

W197661. THE BLOCKER THIS REMOVES, stated first: the fixture image carried a
PROPOSING agent and no integrating one, so the integration container entered
`proposing_entry.py` and proposed instead of importing. The stage went
`exceptional`, and report-and-hold was unreachable by construction -- the same
shape as the earlier blocker, one stage further on.

WHAT THIS IS, SAID PLAINLY AND LABELLED AS SUCH. `integration_workload`'s own
docstring says the PROVIDER performs the import, and that "a host-side copier in
this file wearing the provider's name would be a different capability with the
same result document". That is exactly what this is, and it is a LABELLED
DETERMINISTIC STAND-IN for a model-driven provider turn, in this Work's own
fixture image, so a lifecycle can be proved end to end without a live model. It
claims NO model-driven integration coverage. The real image keeps the real
adapter; nothing here is proposed for it.

WHAT IT MAY NOT DO, and the workload enforces every one of these afterwards:
its own read-back decides `integrated`, not this report; the target's
version-control metadata must not move; and no path outside the scheduled table
may change. This writes exactly the rows the ACCEPTED bundle carries, takes its
bytes from the content-addressed blobs that bundle publishes, and reports what
it did. A report is a claim; the measurement is the workload's.

NOT A SECOND CONTRACT. Every shape here comes from `integration_contract` --
the bundle reader, the blob reader, the report schema and the fixed names -- so
a fixture cannot drift from the document the manager validates.
"""

import json
import os

import integration_contract as contract

__all__ = ["ImportingAgent"]

# THE MODES THE WORKLOAD ADMITS, restated from its own table rather than
# invented: a bundle carrying anything else is refused before this runs.
FILE_MODES = {"100644": 0o644, "100755": 0o755}


class WorkloadRefusal(Exception):
    """This fixture's own refusal; it imports nothing from the manager."""


class ImportingAgent:
    """One provider turn, performed deterministically."""

    def __init__(self, bundle_root=None):
        # AN OPERAND ONLY SO A CASE CAN DRIVE THIS. In a container it is the
        # contract's constant, and a test that could only run against absolute
        # container paths is a test that never runs.
        self.bundle_root = bundle_root or contract.BUNDLE_TARGET

    def invoke_provider(self, *, prompt, room, seen=None):
        """Import the approved rows into `room`, and report what was done.

        THE ANSWER IS THE CLOSED DOCUMENT THE WORKLOAD READS: a dictionary
        carrying `ok`. A turn that could not complete answers `ok: False` with
        its own reason rather than raising, because the workload's vocabulary
        for a failed turn is a HOLD and an exception would be a fault.
        """
        try:
            held = contract.read_bundle(self.bundle_root)
            rows = held["envelope"]["paths"]
            imported = self._imported(rows, room)
            self._reported(prompt, held, imported)
        except KeyError as failure:
            # A MEMBER THIS AGENT EXPECTED AND THE OWNER DOES NOT ANSWER.
            # Measured in the live run of claim201492: `read_bundle` returns
            # `envelope`, `evidence`, `instructions`, `review` and `root` and
            # NO `bundle_digest` -- the workload MEASURES that itself by
            # walking the mounted bundle, and tells the provider in the
            # prompt. My cases mocked `read_bundle`, so the real key set was
            # never exercised and the turn ended as an unexpected fault rather
            # than as a hold this vocabulary has words for.
            return {"ok": False,
                    "failure_reason": f"this runtime expected a bundle member "
                                      f"its owner does not answer: {failure}"}
        except contract.BundleRefusal as failure:
            return {"ok": False, "failure_reason": f"bundle: {failure}"}
        except (WorkloadRefusal, OSError) as failure:
            return {"ok": False,
                    "failure_reason": f"{type(failure).__name__}: {failure}"}
        return {"ok": True, "imported": len(imported)}

    # -- the import ----------------------------------------------------------

    def _imported(self, rows, room):
        """Every scheduled row, and nothing else.

        THE TABLE IS THE SCOPE. The workload compares its own read-back of
        exactly these paths afterwards and holds on any it finds missing, so a
        row skipped here is a hold rather than a silent omission -- and a path
        written that the table does not name is caught by the report check and
        by the target read-back.
        """
        held = os.open(room, os.O_RDONLY | os.O_DIRECTORY)
        try:
            done = []
            for row in rows:
                path = contract.check_bundle_path(row["path"], "a path row")
                candidate = row["candidate"]
                if candidate is None:
                    self._removed(held, path)
                else:
                    self._written(held, path,
                                  contract.bundle_blob(self.bundle_root,
                                                       candidate),
                                  FILE_MODES[candidate["mode"]])
                done.append(path)
        finally:
            os.close(held)
        return sorted(done)

    def _written(self, room, path, payload, mode):
        """One candidate file, written where the row says and nowhere else.

        EVERY COMPONENT RELATIVE TO THE TARGET DESCRIPTOR, no-follow at each
        step, so a link anywhere on the way is refused rather than followed --
        the same rule the capture adapter learned, applied to the one tree this
        runtime may change.
        """
        components = path.split("/")
        here = self._descended(room, components[:-1])
        try:
            name = components[-1]
            # REPLACED THROUGH A STAGING ENTRY rather than truncated in place:
            # an ordinary truncating open follows whatever is at the name, and
            # a half-written candidate is a target the workload read-back
            # would correctly refuse.
            staging = f".{name}.w197661-import"
            handle = os.open(staging,
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW, mode, dir_fd=here)
            try:
                written = 0
                while written < len(payload):
                    moved = os.write(handle, payload[written:])
                    if moved <= 0:
                        raise WorkloadRefusal(
                            f"the target accepted no bytes for {path}")
                    written += moved
            finally:
                os.close(handle)
            # THE MODE IS THE REVIEWED ONE, set explicitly because `O_CREAT`
            # takes the process umask into account and the workload compares
            # the mode it approved.
            os.chmod(staging, mode, dir_fd=here, follow_symlinks=False)
            os.replace(staging, name, src_dir_fd=here, dst_dir_fd=here)
        finally:
            if here != room:
                os.close(here)

    def _removed(self, room, path):
        """One deleted row. Absence is what the read-back looks for."""
        components = path.split("/")
        here = self._descended(room, components[:-1])
        try:
            try:
                os.unlink(components[-1], dir_fd=here)
            except FileNotFoundError:
                pass
        finally:
            if here != room:
                os.close(here)

    def _descended(self, room, components):
        """One directory per component, made if absent, never followed."""
        here = room
        for name in components:
            try:
                os.mkdir(name, 0o755, dir_fd=here)
            except FileExistsError:
                pass
            below = os.open(name,
                            os.O_RDONLY | os.O_NOFOLLOW | os.O_DIRECTORY,
                            dir_fd=here)
            if here != room:
                os.close(here)
            here = below
        return here

    # -- the report ----------------------------------------------------------

    def _reported(self, prompt, held, imported):
        """The bounded report, at the place the prompt names.

        THE PROMPT IS WHERE THE PLACE COMES FROM, because that is how the
        workload tells a provider: it composes the prompt with `report_place`
        and reads back exactly that file. A fixture that guessed a path would
        be answering a different question from the one it was asked.
        """
        place = self._report_place(prompt)
        document = {
            "schema": contract.REPORT_SCHEMA,
            # THE ASSIGNMENT DIGEST IS THE ENVELOPE'S, which it really carries.
            "assignment_digest": held["envelope"]["assignment_digest"],
            # THE BUNDLE DIGEST IS THE PROMPT'S. `read_bundle` does not answer
            # one: `integration_workload` MEASURES the bundle itself -- "a
            # number a bundle states about itself is a claim and this
            # comparison exists to test claims" -- and tells the provider the
            # measured identity in the prompt. Reading it from the bundle was
            # a `KeyError` in the live run, and reading it from the prompt is
            # how the workload actually tells a provider.
            "bundle_digest": self._said(prompt, "Its measured identity is "),
            "outcome": "imported",
            # THE PHASE AN IMPORTED REPORT CARRIES IS `verification`, not
            # `import`. Measured in the live run of claim201492, which held
            # with "its phase or its changed-path list is not the completed
            # turn the target shows": `integration_workload` requires
            # `phase == "verification"` beside an `imported` outcome, because
            # a provider that claims an import while describing a turn that
            # stopped earlier is not corroborating anything. The workload runs
            # the scheduled verification itself afterwards; what this says is
            # that its OWN turn reached the end.
            "phase": "verification",
            "paths": imported,
            # NOTHING MEASURED HERE. The required test is the INTEGRATOR's to
            # run after the import, and a provider claiming a verification it
            # did not perform is the shape this vocabulary exists to refuse.
            "verification": None,
            # `null` IS THE ONLY CODE AN `imported` REPORT CARRIES.
            "code": None}
        payload = json.dumps(document, sort_keys=True).encode()
        scratch, name = os.path.split(place)
        here = os.open(scratch, os.O_RDONLY | os.O_DIRECTORY)
        try:
            handle = os.open(name,
                             os.O_WRONLY | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW, 0o640, dir_fd=here)
            try:
                written = 0
                while written < len(payload):
                    moved = os.write(handle, payload[written:])
                    if moved <= 0:
                        raise WorkloadRefusal(
                            "this runtime's scratch accepted no report bytes")
                    written += moved
            finally:
                os.close(handle)
        finally:
            os.close(here)

    def _report_place(self, prompt):
        """Where the workload asked for the report, read from its own words."""
        for line in (prompt or "").splitlines():
            if "report to " in line and contract.REPORT_SCHEMA in line:
                held = line.split("report to ", 1)[1].strip()
                return held.split(" ")[0].rstrip(".,")
        raise WorkloadRefusal(
            "the prompt names no report place; this runtime writes its report "
            "where it was asked to and nowhere else")

    def _said(self, prompt, marker):
        """One operand the workload stated in its own prompt.

        THE PROMPT IS THE CONTRACT for what a provider is told. Everything
        this reads back is something `compose_prompt` put there in one line.
        """
        for line in (prompt or "").splitlines():
            if line.startswith(marker):
                return line[len(marker):].strip().rstrip(".,")
        raise WorkloadRefusal(
            f"the prompt does not state {marker.strip()!r}; this runtime "
            f"reports the identities it was given rather than ones it "
            f"computed for itself")
