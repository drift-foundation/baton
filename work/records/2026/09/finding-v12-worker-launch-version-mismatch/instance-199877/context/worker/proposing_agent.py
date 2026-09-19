"""The deterministic fixture agent that produces a REAL candidate.

W197661 claim199877. THE BLOCKER THIS REMOVES, stated first: every earlier
fixture wrote `result_metadata: {}` for its `git-change-proposal` output, so it
carried no `baton.git-proposal/1` claim, nothing could be published, and
independent review and report-and-hold were unreachable by construction. The
lifecycle exercise kept stopping at the same wall for a reason that was the
fixture's rather than the deployment's.

WHY IT IS NOT AS HARD AS IT LOOKED. On the `git-line` source profile the
CANDIDATE IS `/output`: `claude_agent` says so in its own words -- "the
workspace IS the durable private repository the manager materialized and
detached before this container existed". So this agent does not have to find,
clone or construct anything. It writes into the tree it was given, commits, and
reports the four facts a proposal claim is made of.

NOT A PROVIDER, AND NOT A STAND-IN FOR ONE. No model is consulted. The change
is derived from the frozen task so two runs of one assignment produce the same
tree, which is what makes a deterministic lifecycle proof possible at all.

WHAT IT MAY NOT SAY, and the rule is `claude_agent`'s: the claim carries what
this turn was built on, what it produced, where its objects are inside its own
declared output, and what it did in words. An artifact id, a content digest, a
byte count or a custody locator would be this container certifying its own
output, and the composer that reads the claim refuses exactly that. The worker
measures the bytes; this file is the least trusted thing in the container.
"""

import json
import os
import subprocess

__all__ = ["ProposingAgent"]

CLAIM_NAMESPACE = "baton.git-proposal/1"
REVIEW_CLAIM_NAMESPACE = "baton.checkpoint-review/1"

OUTPUT_ROOT = "/output"
PROPOSAL = "proposal"
PATCH = "patch.diff"
VERIFICATION = "verification.txt"
RESULT = "result.json"
BUNDLE = "objects.bundle"
MAX_RECAP = 16000

# THE COMMIT'S AUTHOR, on the command line rather than in configuration. The
# container is read-only with a private HOME and no version-control
# configuration at all, so an identity that is not on the argv is not an
# identity -- and one taken from the environment would be whatever the image
# happened to leave behind. Spelled exactly as `claude_agent` spells it.
COMMIT_NAME = "Baton worker"
COMMIT_EMAIL = "worker@baton.invalid"

# WHY EVERY VECTOR CARRIES `safe.directory`: the posture pins one fixed non-root
# uid while the line and its mount are the MANAGER's, so the dubious-ownership
# check applies to a repository this worker was deliberately handed.
VCS = "git"


class WorkloadRefusal(Exception):
    """This turn cannot produce the candidate it was asked for."""


def _ran(repository, *arguments, what):
    """One bounded version-control invocation over the private line."""
    argv = [VCS, "-c", f"safe.directory={repository}",
            "-c", f"user.name={COMMIT_NAME}",
            "-c", f"user.email={COMMIT_EMAIL}",
            "-C", repository, *arguments]
    answer = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    if answer.returncode != 0:
        raise WorkloadRefusal(
            f"{what} failed ({answer.returncode}): "
            f"{(answer.stderr or '').strip()[:400]}")
    return answer.stdout


def _written(place, payload):
    os.makedirs(os.path.dirname(place), exist_ok=True)
    with open(place, "w", encoding="utf-8") as handle:
        handle.write(payload)


class ProposingAgent:
    """Consent and execution, both decided from what was asked."""

    def __init__(self, root=None):
        # THE ROOT IS AN OPERAND ONLY SO A CASE CAN DRIVE THIS. In a container
        # it is the contract's constant; a test that could only run against an
        # absolute container path is a test that never runs.
        self.root = root or OUTPUT_ROOT

    def consider(self, seen, request):
        contract = seen.get("contract", "")
        decision = "decline" if "decline" in contract.lower() else "accept"
        return {"decision": decision,
                "contract_digest": _digest(contract),
                "reason": ("the contract asks for a decline"
                           if decision == "decline"
                           else "the contract is acceptable")}

    def work(self, seen, declared):
        if type(declared) is not list:
            raise WorkloadRefusal("the manager's output declarations are a "
                                  "list")
        if seen.get("role") == "review":
            return self._review(declared)
        return self._propose(seen, declared)

    # -- the implementation turn --------------------------------------------

    def _propose(self, seen, declared):
        """One commit on the private line, and the claim that describes it."""
        base = self._base()
        place = os.path.join(self.root, "w197661-fixture.txt")
        _written(place, "w197661 deterministic fixture candidate\n")
        _ran(self.root, "add", "--", "w197661-fixture.txt",
             what="staging the candidate")
        _ran(self.root, "commit", "--quiet", "--no-gpg-sign",
             "-m", "w197661: the deterministic fixture candidate",
             what="committing the candidate")
        head = _ran(self.root, "rev-parse", "HEAD",
                    what="reading the new head").strip()
        recap = ("the deterministic fixture added w197661-fixture.txt and "
                 "changed nothing else")
        answers, produced = [], []
        for one in declared:
            name, path = one["name"], one["path"]
            if one["type"] == "git-change-proposal":
                self._proposal_tree(path, base, head, recap)
                answers.append({"name": name, "status": "present",
                                "result_metadata": {
                                    CLAIM_NAMESPACE: {
                                        "base": base, "head": head,
                                        "transport": BUNDLE,
                                        "recap": recap[:MAX_RECAP]}}})
            else:
                self._directory(path, name)
                answers.append({"name": name, "status": "present",
                                "result_metadata": {}})
            produced.append(name)
        return {"disposition": "completed", "outputs": answers,
                "recap": ("the deterministic fixture produced "
                          + ", ".join(produced))[:MAX_RECAP]}

    def _proposal_tree(self, path, base, head, recap):
        """The declared tree: a patch, a transcript, a record and the objects.

        NO CANDIDATE COPY. The candidate is a commit on a durable private line,
        so a second copy of its files beside it would be another account of the
        same bytes for somebody to reconcile.
        """
        proposal = os.path.join(self.root, path)
        os.makedirs(proposal, exist_ok=True)
        _written(os.path.join(proposal, PATCH),
                 _ran(self.root, "diff", "--no-renames", f"{base}..{head}",
                      what="the proposed patch"))
        _written(os.path.join(proposal, VERIFICATION),
                 "no verification was attempted by this deterministic "
                 "fixture\n")
        _written(os.path.join(proposal, RESULT),
                 json.dumps({"recap": recap, "base": base, "head": head},
                            indent=1, sort_keys=True) + "\n")
        # THE OBJECTS LAST AND ONLY WITH A HEAD, and a stale one removed first:
        # on a persistent line the declared directory SURVIVES the turn that
        # wrote it, so a previous attempt's objects sitting here would be
        # collected as though this turn had claimed them.
        objects = os.path.join(proposal, BUNDLE)
        if os.path.lexists(objects):
            os.unlink(objects)
        _ran(self.root, "bundle", "create", "--quiet", objects,
             f"{base}..HEAD", what="the proposed objects")

    def _directory(self, path, name):
        place = os.path.join(self.root, path)
        os.makedirs(place, exist_ok=True)
        _written(os.path.join(place, "result.txt"),
                 f"the deterministic fixture produced {name}\n")

    def _base(self):
        """The revision this turn is offered against, from the frozen task.

        THE IMMUTABLE ONE. On a correction round it is still the revision the
        proposal is offered against rather than the head the turn started from:
        the publication driver requires the proposal's source base to be the
        canonical target, and an entry head is not that.
        """
        place = os.path.join("/input", "task.json")
        try:
            with open(place, encoding="utf-8") as handle:
                return json.load(handle)["declared_base"]
        except (OSError, ValueError, KeyError):
            # THE LINE'S OWN CURRENT HEAD, which is what the manager detached
            # this worktree at. A case driving this without an input root gets
            # the same answer the container would.
            return _ran(self.root, "rev-parse", "HEAD",
                        what="reading the declared base").strip()

    # -- the review turn -----------------------------------------------------

    def _review(self, declared):
        """A verdict about the frozen checkpoint this container was given.

        IT EDITS NOTHING. A review reads a frozen checkpoint and decides about
        it; the three observations are the line's own and the verdict is
        deterministic, so a fixture can assert an exact outcome without this
        pretending to judge.
        """
        head = _ran(self.root, "rev-parse", "HEAD",
                    what="the reviewed head").strip()
        tree = _ran(self.root, "rev-parse", "HEAD^{tree}",
                    what="the reviewed tree").strip()
        base = _ran(self.root, "rev-parse", "HEAD~1",
                    what="the reviewed base").strip()
        answers = []
        for one in declared:
            name, path = one["name"], one["path"]
            self._directory(path, name)
            answers.append({
                "name": name, "status": "present",
                "result_metadata": ({REVIEW_CLAIM_NAMESPACE: {
                    "base": base, "head": head, "tree": tree,
                    "verdict": "accepted"}}
                    if name == "findings" else {})})
        return {"disposition": "completed", "outputs": answers,
                "recap": "the deterministic fixture reviewed the checkpoint "
                         "and accepted it"}


def _digest(value):
    import hashlib

    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()
