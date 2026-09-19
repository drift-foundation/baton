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

# THE READ-ONLY INPUT ROOT, and on a REVIEW turn it is where the checkpoint is.
# W197661 review200179 [R1]: this fixture asked `self.root` -- the reviewer's
# separate WRITABLE result directory -- for head, tree and parent, which is a
# verdict about the wrong objects entirely. The real adapter reads
# `/input/<task.source_root>`: `review_cycles.review_boundary` nominates the
# line and `source_boundary` binds it read-only there, beside the separate
# writable workspace. Two roots, and a review that conflates them is reviewing
# its own output.
INPUT_ROOT = "/input"

# The frozen task, in the read-only input root. It carries the declared base,
# which is the revision a verdict is ABOUT -- `HEAD~1` is this fixture guessing
# at the shape of a line rather than reading what it was told.
TASK_DOCUMENT = "task.json"

# The repository's own metadata directory, where a local exclude file lives.
VCS_METADATA = ".git"

# The worker's own completion envelope, written into this same workspace after
# the turn returns. Reserved with the declared outputs for the same reason.
ENVELOPE = "output.json"
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

    def __init__(self, root=None, inputs=None):
        # TWO ROOTS, because the contract has two. `root` is the WRITABLE
        # result directory this turn owns; `inputs` is the READ-ONLY input
        # root, and on a review turn it holds the frozen checkpoint. They are
        # operands only so a case can drive this -- in a container they are the
        # contract's constants, and a test that could only run against absolute
        # container paths is a test that never runs.
        #
        # THEY ARE NEVER THE SAME DIRECTORY here by default. Review200179 found
        # this fixture's review turn reading `self.root`, and the three review
        # cases hid it by handing the implementation repository in as the
        # review OUTPUT root.
        self.root = root or OUTPUT_ROOT
        self.inputs = inputs or INPUT_ROOT

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
        # THE DECLARED OUTPUTS ARE NOT PART OF THE CANDIDATE, and the line has
        # to be told so BEFORE they are written. W197661 c200000, found by
        # running the installed lifecycle: `checkpoint_profiles.freeze` refuses
        # a line with "tracked or untracked worktree changes", and on the
        # git-line profile the declared outputs are written INTO the worktree
        # -- so writing them is exactly what made the line dirty. The whole
        # lifecycle stopped at `freeze_checkpoint` with the candidate already
        # committed.
        #
        # THE REAL ADAPTER ALREADY DOES THIS and this follows it rather than
        # inventing something: `claude_agent._reserve` writes the reserved
        # names into the repository's own local exclude file, root-anchored. A
        # committed ignore file would be this turn proposing a change to
        # somebody else's tree; a global one would outlive the container. This
        # is repository-local, never committed, and dies with the line.
        self._reserve(declared)
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

    def _reserve(self, declared):
        """Every declared output path, put out of the candidate's reach.

        ROOT-ANCHORED, so `proposal` reserves the workspace's own declared
        directory and not a directory of that name inside the candidate. The
        file is REPLACED rather than appended, so a resumed turn reserves
        exactly this set.
        """
        reserved = set()
        for one in declared:
            path = one.get("path")
            if type(path) is not str or not path:
                raise WorkloadRefusal("a declared output names a path")
            reserved.add(path.strip("/").split("/")[0])
        # THE COMPLETION ENVELOPE TOO. The worker writes it into this same
        # workspace after this turn returns, and a line dirtied after the turn
        # is a line this turn cannot see.
        reserved.add(ENVELOPE)
        place = os.path.join(self.root, VCS_METADATA, "info")
        os.makedirs(place, exist_ok=True)
        _written(os.path.join(place, "exclude"),
                 "".join("/%s\n" % name for name in sorted(reserved)))

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
        found = self._task()
        if found is not None and type(found.get("declared_base")) is str:
            return found["declared_base"]
        # THE LINE'S OWN CURRENT HEAD, which is what the manager detached this
        # worktree at. An IMPLEMENTATION turn can fall back to it because the
        # line it was handed is the thing it is building on; a review turn
        # cannot, and `_review` refuses instead.
        return _ran(self.root, "rev-parse", "HEAD",
                    what="reading the declared base").strip()

    def _task(self):
        """The frozen task, from the READ-ONLY input root, or None."""
        try:
            with open(os.path.join(self.inputs, TASK_DOCUMENT),
                      encoding="utf-8") as handle:
                found = json.load(handle)
        except (OSError, ValueError):
            return None
        return found if type(found) is dict else None

    # -- the review turn -----------------------------------------------------

    def _review(self, declared):
        """A verdict about the frozen checkpoint this container was given.

        TWO ROOTS, AND THE CHECKPOINT IS IN THE READ-ONLY ONE. Review200179
        [R1]: this asked `self.root` -- the reviewer's separate WRITABLE result
        directory -- for head, tree and parent, so the verdict was about
        whatever happened to be in the output root. The line is bound read-only
        at `/input/<task.source_root>`, which is where the real adapter reads
        it, and the findings and logs still go to the output root and nowhere
        else.

        IT EDITS NOTHING, and now the arrangement says so rather than the
        intention: every observation is taken from a mount the container cannot
        write to.

        THE BASE IS READ, NOT GUESSED. `HEAD~1` was this fixture assuming the
        shape of a line; the declared base is the revision the verdict is
        about, and it is PROVED against the line rather than echoed -- the same
        distinction `claude_agent._observed` makes, because `rev-parse
        --verify` accepts a well-formed name as syntax whether or not the
        repository holds the object.

        MISSING OR INCORRECT INPUT REFUSES. Falling back to the output root is
        how the defect above reads correct.
        """
        found = self._task()
        if found is None:
            raise WorkloadRefusal(
                f"a review turn reads its frozen task at "
                f"{os.path.join(self.inputs, TASK_DOCUMENT)} and there is no "
                f"readable document there; this turn will not review its own "
                f"output root instead")
        root = found.get("source_root")
        declared_base = found.get("declared_base")
        if type(root) is not str or not root or "/" in root:
            raise WorkloadRefusal(
                "a review turn's frozen task names one source_root inside the "
                "read-only input root")
        if type(declared_base) is not str or not declared_base:
            raise WorkloadRefusal(
                "a review turn's frozen task names the declared base its "
                "verdict is about; a base this fixture guessed would be a "
                "verdict about a revision nobody nominated")
        source = os.path.join(self.inputs, root)
        if not os.path.isdir(source):
            raise WorkloadRefusal(
                f"the reviewed line is read at {source} and there is no "
                f"directory there")
        base = _ran(source, "rev-parse", "--verify", "--quiet",
                    f"{declared_base}^{{commit}}",
                    what="the reviewed base").strip()
        if base != declared_base:
            raise WorkloadRefusal(
                f"this review task declares base {declared_base!r} and the "
                f"line resolves it to {base!r}; a review names the object it "
                f"read")
        head = _ran(source, "rev-parse", "HEAD",
                    what="the reviewed head").strip()
        tree = _ran(source, "rev-parse", "HEAD^{tree}",
                    what="the reviewed tree").strip()
        answers = []
        for one in declared:
            name, path = one["name"], one["path"]
            # INTO THE OUTPUT ROOT AND NOWHERE ELSE. `_directory` resolves
            # against `self.root`, which is the writable one.
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
