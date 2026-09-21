"""Record a HUMAN-accepted base on an installed instance, exactly once.

W202663, OWNER-HANDOFF-PR-JOBS item 4, pinned at claim220385, amended by
review220421 and corrected under review221684. In the owner-selected PR
model, Slawomir merges reviewed candidates on the official line and the
accepted commit becomes the next base. `bootstrap.admissible_bases` admits
a new Job on an ESTABLISHED root only at the Authority's current canonical
target, so the acceptance has to be RECORDED as a supported transition --
this verb -- or the deployment can never continue past its first base
without a reinstall.

THE THREE MEASURED CORRECTIONS (review221684), each one a probe:

- [R1] Holding the lifecycle flock never meant STOPPED: `stack.start`
  releases it when start returns, and O_CLOEXEC keeps it out of the
  children. So this tool takes the stack's own `admission` AND proves the
  recorded manager and publisher processes are positively not running
  (`stack.ownership`: absent or gone; live or unknown refuses) -- the same
  liveness proof `stop` trusts, held under the same lock every lifecycle
  transition serializes on.
- [R2] The reference used to advance BEFORE a stale Authority refusal.
  Now the FULL document validates first, and the Authority's canonical
  target and the reference are both read and judged BEFORE any repository
  effect: a stale policy, a foreign reference, or a coincidence refuses
  while the repository still holds exactly what it held. The fetch that
  supplies the accepted objects runs only after both prechecks pass; on a
  later refusal those objects remain as RECOVERABLE SAME-OPERATION partial
  state -- additive, named here, never called "nothing happened".
- [R3] A receipt FILE alone is not authority. Replay requires the receipt
  to name this acceptance's operation id, carry byte-identical acceptance
  content, AND match the Authority's own COMMITTED operation result for
  that identity. A fabricated, partial or tampered receipt refuses; a
  legitimate historical receipt stays valid after LATER acceptances (its
  operation committed; nothing rewinds a newer base). A reference
  coincidentally at the accepted commit is not this invocation's resume
  unless prior evidence -- a byte-identical intent or the committed
  operation -- says so.

DURABILITY: intent and receipt writes stage, fsync the file, `os.replace`,
and fsync the containing directory, so the durable-before-effects order is
real rather than named. The `accepted-bases` custody directory is 0o700.

    PYTHONPATH=src:. python3 -m tools.accepted_base \
        --instance <state root> --acceptance <acceptance.json>
"""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

SCHEMA = "baton.w202663.accepted-base/1"
RECEIPT_SCHEMA = "baton.w202663.accepted-base-receipt/1"
MEMBERS = ("schema", "repository", "accepted_commit", "expected_old",
           "included_candidates", "acceptance_evidence", "accepted_by",
           "recorded_at")
ADMISSION_WAIT = 2.0


class Refused(SystemExit):
    def __init__(self, message):
        super().__init__(f"refused: {message}")


def _canonical(document):
    return json.dumps(document, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _now():
    held = datetime.datetime.now(datetime.timezone.utc)
    return (held.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{held.microsecond // 1000:03d}Z")


def _ran(*argv, allowed=(0,)):
    answer = subprocess.run(list(argv), capture_output=True, text=True,
                            timeout=300)
    if answer.returncode not in allowed:
        raise Refused(f"{' '.join(argv[:3])}... exited "
                      f"{answer.returncode}: {answer.stderr.strip()[:400]}")
    return answer


def _durable_write(place, payload):
    """Staged, WHOLLY written, synced, replaced, and the DIRECTORY synced:
    durable, not merely atomic naming. `os.write` may write fewer bytes
    than asked and does not call that an error (review221748), so every
    byte is accounted and no progress refuses."""
    staged = place.with_suffix(".staging")
    handle = os.open(staged, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        written = 0
        while written < len(payload):
            step = os.write(handle, payload[written:])
            if type(step) is not int or step <= 0:
                raise Refused(f"writing {place.name} made no progress after "
                              f"{written} of {len(payload)} bytes; a partly "
                              f"written record must not become durable")
            written += step
        os.fsync(handle)
    finally:
        os.close(handle)
    os.replace(staged, place)
    _sync_directory(place.parent)


def _durable_directory(place):
    """A custody directory whose ENTRY is durable before anything inside it:
    made if absent, then its PARENT synced, in creation order."""
    made = not place.is_dir()
    place.mkdir(mode=0o700, exist_ok=True)
    if made:
        _sync_directory(place.parent)


def _sync_directory(place):
    handle = os.open(place, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(handle)
    finally:
        os.close(handle)


def _validated(document):
    """The FULL document, judged before any effect anywhere (R2)."""
    if type(document) is not dict or any(one not in document
                                         for one in MEMBERS):
        raise Refused("an acceptance document carries schema, repository, "
                      "accepted_commit, expected_old, included_candidates, "
                      "acceptance_evidence, accepted_by and recorded_at")
    if document["schema"] != SCHEMA:
        raise Refused(f"an acceptance document's schema is {SCHEMA}")
    for member in ("accepted_commit", "expected_old"):
        value = document[member]
        if (type(value) is not str or len(value) != 40
                or any(one not in "0123456789abcdef" for one in value)):
            raise Refused("accepted_commit and expected_old are "
                          "40-lowercase-hex commits")
    if document["accepted_commit"] == document["expected_old"]:
        raise Refused("accepted_commit equal to expected_old moves nothing")
    if type(document["repository"]) is not str or not document["repository"]:
        raise Refused("repository names where the accepted commit lives")
    return document


def _stopped(state_dir):
    """The stack's OWN liveness proof, under its own admission (R1)."""
    from tools import stack

    for name in ("manager", "publisher"):
        held = stack.ownership(stack.read_record(str(state_dir), name))
        if held not in (stack.ABSENT, stack.GONE):
            raise Refused(f"the instance's {name} is {held}; an acceptance "
                          f"is recorded on a STOPPED instance, proved by "
                          f"the stack's own ownership records rather than "
                          f"assumed from a lock")


def _committed(root, uuid, operation_id):
    """The Authority's own committed answer for this identity, or None."""
    from baton_v12.authority import Authority

    authority = Authority.open_readonly(
        str(root / "db" / "authority.sqlite3"),
        expected_authority_uuid=uuid)
    try:
        answer = authority.operation_result(operation_id)
        target = authority.canonical_target()
    finally:
        dispose = getattr(authority, "dispose", None)
        if dispose is not None:
            dispose()
    return answer, target


def _finalize(receipt, document, answer, operation_id, intent):
    _durable_directory(receipt.parent)
    finished = {"schema": RECEIPT_SCHEMA, "acceptance": document,
                "authority": answer, "operation_id": operation_id,
                "performed_at": _now()}
    _durable_write(receipt, json.dumps(finished, indent=2, sort_keys=True)
                   .encode("utf-8") + b"\n")
    try:
        os.unlink(intent)
        _sync_directory(intent.parent)
    except OSError:
        pass


def main(argv=None):
    parser = argparse.ArgumentParser(prog="accepted_base")
    parser.add_argument("--instance", required=True,
                        help="the installed instance's state root")
    parser.add_argument("--acceptance", required=True,
                        help="the acceptance document (JSON file)")
    taken = parser.parse_args(argv)

    # [R2] EVERYTHING JUDGEABLE WITHOUT EFFECTS IS JUDGED FIRST.
    document = _validated(json.loads(Path(taken.acceptance).read_text()))
    root = Path(taken.instance)
    identity_place = root / "authority-identity.json"
    if not identity_place.is_file():
        raise Refused(f"{root} is not an installed instance")
    uuid = json.loads(identity_place.read_text())["authority_uuid"]
    target_git = root / "repo" / "target.git"
    if not target_git.is_dir():
        raise Refused(f"{target_git} is not here")

    payload = _canonical(document)
    identity = hashlib.sha256(payload).hexdigest()
    operation_id = f"accepted-base:{identity}"
    custody = root / "accepted-bases"
    intent = custody / "intents" / f"{identity}.json"
    receipt = custody / f"{identity}.json"
    accepted = document["accepted_commit"]
    expected = document["expected_old"]

    from tools import stack

    try:
        with stack.admission(str(root / "state"), wait=ADMISSION_WAIT):
            return _admitted(document, root, uuid, target_git, payload,
                             operation_id, custody, intent, receipt,
                             accepted, expected)
    except stack.StackRefusal as refusal:
        raise Refused(str(refusal))


def _admitted(document, root, uuid, target_git, payload, operation_id,
              custody, intent, receipt, accepted, expected):
    """Everything that happens INSIDE the held lifecycle admission."""
    if True:
        # [R1] the lock serializes lifecycle transitions; STOPPED is proved.
        _stopped(root / "state")

        # [R3] a receipt replays only against its COMMITTED operation.
        if receipt.is_file():
            try:
                held = json.loads(receipt.read_text())
            except ValueError:
                raise Refused("the receipt under this identity does not "
                              "decode; a tampered receipt is not authority")
            if (type(held) is not dict
                    or held.get("schema") != RECEIPT_SCHEMA
                    or held.get("operation_id") != operation_id
                    or _canonical(held.get("acceptance", {})) != payload):
                raise Refused("the receipt under this identity does not "
                              "carry this acceptance and its operation; a "
                              "receipt is evidence of one committed act, "
                              "not a file that ends the check")
            answer, _target = _committed(root, uuid, operation_id)
            if (type(answer) is not dict
                    or answer.get("kind") != "accepted-base"
                    or answer.get("accepted_commit") != accepted):
                raise Refused("the receipt's operation never committed in "
                              "this Authority; a local file alone is not a "
                              "replayed acceptance")
            # HISTORICAL RECEIPTS STAY VALID after later acceptances: the
            # committed operation is the evidence, and nothing rewinds a
            # newer base here.
            print(json.dumps({"recorded": False, "replayed": True,
                              "receipt": str(receipt)}, indent=1))
            return 0

        # THE INITIAL STATE IS JUDGED BEFORE ANY INTENT IS PUBLISHED
        # (review221748): the intent is what grants a later invocation
        # resume authority, so a state this invocation would REFUSE must
        # never leave one behind -- the probe showed a refused first call
        # writing the intent and an identical second call trusting it and
        # advancing the Authority. Only a byte-identical intent that was
        # ALREADY THERE counts as prior evidence; this invocation publishes
        # its own intent strictly after every admission check passes.
        resumed = False
        if intent.is_file():
            if intent.read_bytes() != payload:
                raise Refused("an intent exists under this identity whose "
                              "document differs; refuse rather than resume "
                              "somebody else's acceptance")
            resumed = True

        # [R2] BOTH targets judged BEFORE any repository effect.
        answer, target = _committed(root, uuid, operation_id)
        current = _ran("git", "--git-dir", str(target_git), "rev-parse",
                       "refs/heads/main").stdout.strip()
        if answer is not None:
            # The operation committed and only the receipt is missing: the
            # crash window between the Authority write and finalization.
            if (answer.get("kind") != "accepted-base"
                    or answer.get("accepted_commit") != accepted):
                raise Refused("the committed operation under this identity "
                              "is not this acceptance")
            _finalize(receipt, document, answer, operation_id, intent)
            print(json.dumps({"recorded": False, "replayed": True,
                              "finalized_receipt": True,
                              "receipt": str(receipt)}, indent=1))
            return 0
        if target == accepted:
            raise Refused("the canonical target already names the accepted "
                          "commit under another operation; nothing here "
                          "synthesizes an acceptance from a coinciding "
                          "value")
        if target != expected:
            raise Refused("the canonical target is not the acceptance's "
                          "expected_old; the acceptance was taken against "
                          "a target that has moved, and neither the "
                          "reference nor the repository was touched")
        if current == accepted:
            if not resumed:
                raise Refused("refs/heads/main already names the accepted "
                              "commit and no prior intent or committed "
                              "operation says this invocation put it "
                              "there; a coincidence is not a resume")
        elif current != expected:
            raise Refused(f"refs/heads/main is {current}, neither the "
                          f"acceptance's expected_old nor its accepted "
                          f"commit; neither the reference nor the "
                          f"repository was touched")

        # ADMITTED: publish this invocation's own durable intent, then the
        # effect phase begins. Custody directories are made durable in
        # ORDER -- each new directory's PARENT is synced before anything is
        # written inside it (review221748's durability completion).
        if not resumed:
            _durable_directory(custody)
            _durable_directory(intent.parent)
            _durable_write(intent, payload)

        # The accepted objects, present in the dedicated target. Additive:
        # on any later refusal they remain as recoverable same-operation
        # partial state, and this tool says so rather than claiming zero
        # effects. `cat-file -e` answers 128 for an absent object under the
        # ^{commit} peel -- the ordinary miss; the strict recheck after the
        # fetch is what refuses a repository that cannot answer.
        present = _ran("git", "--git-dir", str(target_git), "cat-file",
                       "-e", f"{accepted}^{{commit}}", allowed=(0, 1, 128))
        if present.returncode != 0:
            _ran("git", "--git-dir", str(target_git), "fetch",
                 document["repository"], accepted)
            _ran("git", "--git-dir", str(target_git), "cat-file", "-e",
                 f"{accepted}^{{commit}}")

        if current != accepted:
            _ran("git", "--git-dir", str(target_git), "update-ref",
                 "refs/heads/main", accepted, expected)

        from baton_v12.authority import Authority, Refusal

        authority = Authority.open(str(root / "db" / "authority.sqlite3"),
                                   expected_authority_uuid=uuid)
        try:
            try:
                answer = authority.accept_base(document,
                                               operation_id=operation_id)
            except Refusal as refusal:
                raise Refused(str(refusal))
        finally:
            dispose = getattr(authority, "dispose", None)
            if dispose is not None:
                dispose()

        _finalize(receipt, document, answer, operation_id, intent)
        print(json.dumps({"recorded": True, "receipt": str(receipt),
                          "authority": answer}, indent=1))
        return 0


if __name__ == "__main__":
    sys.exit(main())
