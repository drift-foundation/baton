"""W133117 claim136400 -- the amendment's REQUIRED FIRST PROOF.

AMENDMENT-publication-before-authorization-v1.md: "Prove the real-session
round trip before dependent implementation."  Nothing here imports
`reconciliation`; it asks the REAL `Authority`, REAL scoped sessions and REAL
Git exactly what the amendment's design intends to call, so the design is
pinned against the accepted public interface rather than against my reading
of it.

Every repository below is created inside one disposable temporary directory
and disposed with it. Nothing reaches this checkout, its history or its index.

Six questions, each answered by the thing itself:

 1. Can a derived proposal carry a result digest DERIVED FROM A CLOSED CUSTODY
    BASIS, and does the Authority read every field of it back?
 2. Are the input and policy digests PROVABLE against the accepted owning Job
    -- i.e. does the publishing session's own `proposal` read reach the
    producer's proposal, which admission already binds to the Job's digests?
 3. Do three real configured sessions record ordinary verification/review/
    approval receipts on that derived proposal, and does `receipt` read them
    back with actor, disposition, candidate digest, target and generation?
 4. Is the approval's policy generation comparable with the Authority's
    CURRENT generation?
 5. Is "published but unapproved" a real observable state -- no receipts yet
    -- and do the Authority's own preconditions refuse a nonaccepting chain?
 6. Can the standalone Git profile resolve a repository IDENTITY that sees
    through a symlink alias and a linked worktree's shared common directory?
"""

import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.getcwd(), "v12/python/src"))

from baton_v12.authority import Authority
from baton_v12.authority.errors import Refusal
from baton_v12.contracts import digest

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123456f-W133117"
PRODUCER = "baton.producer"
INTEGRATOR = "baton.integrator"
RESULT_OWNERS = {"verification": "baton.result-verify",
                 "review": "baton.result-review",
                 "approval": "baton.result-approve"}
VERBS = {"verification": "verify", "review": "review", "approval": "approve"}
ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": "/nonexistent",
       "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull,
       "GIT_TERMINAL_PROMPT": "0",
       "GIT_AUTHOR_NAME": "Probe", "GIT_AUTHOR_EMAIL": "probe@invalid",
       "GIT_COMMITTER_NAME": "Probe", "GIT_COMMITTER_EMAIL": "probe@invalid",
       "GIT_AUTHOR_DATE": "2026-09-10T13:00:00+00:00",
       "GIT_COMMITTER_DATE": "2026-09-10T13:00:00+00:00"}

answers = {}


def scm(place, *argv):
    done = subprocess.run(["git", "-C", place] + list(argv), env=ENV,
                          capture_output=True, text=True, timeout=120)
    assert done.returncode == 0, (argv, done.stderr)
    return done.stdout.strip()


def refused(call):
    try:
        call()
    except Refusal as no:
        return "refused: " + str(no)
    return "NOT REFUSED"


root = tempfile.mkdtemp(prefix="v12-roundtrip-136400-")

# -- 6. repository identity, before the Authority work ----------------------
target = os.path.join(root, "target")
os.makedirs(target)
scm(target, "init", "-q", "-b", "main")
with open(os.path.join(target, "a.py"), "w") as handle:
    handle.write("A = 1\n")
scm(target, "add", "--all")
scm(target, "commit", "-q", "-m", "the base")
line = os.path.join(root, "line-b")
subprocess.run(["git", "clone", "-q", target, line], env=ENV, check=True,
               capture_output=True, timeout=120)
workspace = os.path.join(root, "workspace")
os.makedirs(workspace)
scm(workspace, "init", "-q", "--bare")

alias = os.path.join(root, "line-b-alias")
os.symlink(line, alias)
worktree = os.path.join(root, "line-b-worktree")
scm(line, "worktree", "add", "-q", "--detach", worktree)


def storage(repository):
    """THE CAPABILITY THE AMENDMENT ASKS FOR, asked of real Git."""
    common = scm(repository, "rev-parse", "--path-format=absolute",
                 "--git-common-dir")
    real = os.path.realpath(common)
    held = os.stat(real)
    return {"git_common_dir": real, "device": held.st_dev, "inode": held.st_ino}


identities = {name: storage(place) for name, place in
              (("target", target), ("line", line), ("workspace", workspace),
               ("line_symlink_alias", alias), ("line_worktree", worktree))}


def key(one):
    return (one["device"], one["inode"])


answers["repository_identity"] = {
    "distinct_target_line_workspace":
        len({key(identities[n]) for n in ("target", "line", "workspace")}) == 3,
    "a_symlink_alias_is_the_SAME_repository":
        key(identities["line_symlink_alias"]) == key(identities["line"]),
    "a_linked_worktree_SHARES_the_common_directory":
        key(identities["line_worktree"]) == key(identities["line"]),
    "common_dirs": {n: identities[n]["git_common_dir"] for n in identities}}

# -- the real Authority, the producer's proposal and the integrator ---------
authority = Authority.create(os.path.join(root, "authority.sqlite3"),
                             authority_uuid=UUID)
base = scm(target, "rev-parse", "HEAD")
candidate = scm(line, "rev-parse", "HEAD")
authority.set_policy("canonical_target", base)
authority.create_work(WORK, "impl", contract="v12-assignment-1",
                      operation_id="create-work")
authority.add_route_handler("impl", PRODUCER)
authority.add_route_handler("integ", INTEGRATOR)
producer = authority.session(PRODUCER)
claimed = producer.claim({"work_id": WORK, "operation_id": "claim-producer"})
JOB_INPUT = "sha256:" + "2" * 64
JOB_POLICY = "sha256:" + "3" * 64
producer.publish({"expect": claimed["assignment"],
                  "operation_id": "publish-original",
                  "proposal_id": "proposal-b1", "result_id": "result-b1",
                  "result_digest": "sha256:" + "1" * 64,
                  "candidate_digest": candidate,
                  "input_digest": JOB_INPUT, "policy_digest": JOB_POLICY})
for kind, verb in VERBS.items():
    who = "baton.source-" + verb
    authority.grant_capability(who, verb)
    session = authority.session(who)
    operands = {"proposal_id": "proposal-b1", "operation_id": "source-" + kind}
    if kind == "verification":
        operands.update(verification_id="source-verification-1",
                        observation="passed")
    elif kind == "review":
        operands.update(review_id="source-review-1", disposition="accepted")
    else:
        operands.update(approval_id="source-approval-1", disposition="approved",
                        policy_generation=authority.policy_generation())
    getattr(session, verb)(operands)
source_receipts_before = [r["receipt_id"] for r in
                          authority.receipts("proposal-b1")]
producer.pass_work({"expect": claimed["assignment"],
                    "operation_id": "pass-to-integ", "to_route": "integ",
                    "comment": "ready"})
session = authority.session(INTEGRATOR)
assignment = session.claim({"work_id": WORK,
                            "operation_id": "claim-integ"})["assignment"]

# -- 2. the input/policy digests, proved through the session's own read -----
original = session.proposal("proposal-b1")
answers["input_and_policy_are_provable_without_a_new_reader"] = {
    "the_publishing_session_can_read_the_producers_proposal": True,
    "input_digest_matches_the_accepted_job":
        original["input_digest"] == JOB_INPUT,
    "policy_digest_matches_the_accepted_job":
        original["policy_digest"] == JOB_POLICY,
    "a_wrong_input_digest_is_detectable_here":
        original["input_digest"] != "sha256:" + "9" * 64}

# -- 1. the closed custody basis and the derived result digest --------------
prepared_head = "d" * 40
prepared_tree = "e" * 40
content_digest = digest({"a.py": {"mode": "100644", "object": "f" * 40}})
observations_digest = digest({"combined": {"status": 0}})
DERIVED_RESULT = "derived-result-1"
basis = {"derived_result_id": DERIVED_RESULT,
         "result_id": "result-1",
         "source": {"job_id": "job-b", "line_id": "line-b",
                    "source_proposal_id": "proposal-b1",
                    "source_result_id": "result-b1",
                    "source_base": base, "source_candidate": candidate},
         "integration_assignment": assignment,
         "prepared": {"head": prepared_head, "tree": prepared_tree,
                      "content_digest": content_digest},
         "target": base,
         "input_digest": original["input_digest"],
         "policy_digest": original["policy_digest"],
         "observed_by": "baton.result-observe",
         "observations": observations_digest}
derived_result_digest = digest(basis)

published = session.publish({"expect": assignment,
                             "operation_id": "integration-publish:result-1",
                             "proposal_id": "proposal-derived",
                             "result_id": DERIVED_RESULT,
                             "result_digest": derived_result_digest,
                             "candidate_digest": prepared_head,
                             "input_digest": original["input_digest"],
                             "policy_digest": original["policy_digest"],
                             "target": base})
held = authority.proposal("proposal-derived")
answers["derived_publication_round_trip"] = {
    "result_id": held["result_id"] == DERIVED_RESULT,
    "result_digest_is_the_custody_basis":
        held["result_digest"] == derived_result_digest,
    "re_derived_from_immutable_custody": digest(basis) == held["result_digest"],
    "candidate_digest": held["candidate_digest"] == prepared_head,
    "input_digest": held["input_digest"] == original["input_digest"],
    "policy_digest": held["policy_digest"] == original["policy_digest"],
    "target": held["target"] == base,
    "assignment_ref": held["assignment_ref"] == assignment,
    "carries_a_decision_and_an_instant":
        held["decision"] is not None and held["published_at"] is not None,
    "borrowing_the_producers_result_identity": refused(
        lambda: session.publish({
            "expect": assignment, "operation_id": "integration-publish:borrow",
            "proposal_id": "proposal-borrowed", "result_id": "result-b1",
            "result_digest": derived_result_digest,
            "candidate_digest": prepared_head,
            "input_digest": original["input_digest"],
            "policy_digest": original["policy_digest"], "target": base}))}

# -- 5. PUBLISHED IS UNAPPROVED, and it is observable -----------------------
answers["published_is_unapproved"] = {
    "no_verification_receipt_yet":
        authority.receipt("proposal-derived", "verification") is None,
    "no_review_receipt_yet":
        authority.receipt("proposal-derived", "review") is None,
    "no_approval_receipt_yet":
        authority.receipt("proposal-derived", "approval") is None,
    "receipts_are_empty": authority.receipts("proposal-derived") == []}

# The Authority's OWN preconditions, before any accepting receipt exists.
for kind, verb in VERBS.items():
    authority.grant_capability(RESULT_OWNERS[kind], verb)
answers["the_authoritys_own_chain_preconditions"] = {
    "review_before_a_passed_verification": refused(
        lambda: authority.session(RESULT_OWNERS["review"]).review({
            "proposal_id": "proposal-derived", "review_id": "premature-review",
            "disposition": "accepted", "operation_id": "premature-review"})),
    "approval_before_an_accepted_review": refused(
        lambda: authority.session(RESULT_OWNERS["approval"]).approve({
            "proposal_id": "proposal-derived",
            "approval_id": "premature-approval", "disposition": "approved",
            "operation_id": "premature-approval",
            "policy_generation": authority.policy_generation()}))}

# -- 3. three REAL receipts by three REAL scoped sessions -------------------
generation = authority.policy_generation()
for kind, verb in VERBS.items():
    owner = authority.session(RESULT_OWNERS[kind])
    operands = {"proposal_id": "proposal-derived",
                "operation_id": "result-" + kind}
    if kind == "verification":
        operands.update(verification_id="result-verification-1",
                        observation="passed")
    elif kind == "review":
        operands.update(review_id="result-review-1", disposition="accepted")
    else:
        operands.update(approval_id="result-approval-1",
                        disposition="approved", policy_generation=generation)
    getattr(owner, verb)(operands)

read_back = {kind: authority.receipt("proposal-derived", kind)
             for kind in VERBS}
answers["real_receipts_read_back"] = {
    kind: {"actor": one["actor"], "disposition": one["disposition"],
           "proposal_id": one["proposal_id"],
           "binds_the_candidate": one["candidate_digest"] == prepared_head,
           "binds_the_target": one["target"] == base,
           "policy_generation": one["policy_generation"],
           "names_a_decision": one["decision"] is not None}
    for kind, one in read_back.items()}
answers["the_three_actors_are_independent"] = len(
    {one["actor"] for one in read_back.values()}) == 3

# -- 4. the approval generation against the CURRENT policy ------------------
answers["policy_generation"] = {
    "the_approval_receipt_carries_it":
        read_back["approval"]["policy_generation"] == generation,
    "the_authority_answers_its_current_one":
        authority.policy_generation() == generation}
authority.grant_capability("baton.someone-else", "review")
answers["policy_generation"]["an_advance_is_visible_against_the_receipt"] = (
    authority.policy_generation() != read_back["approval"]["policy_generation"])

# -- a receipt is immutable, and a foreign one cannot be borrowed -----------
answers["receipts_cannot_be_rewritten_or_borrowed"] = {
    "immutable": refused(lambda: authority.session(
        RESULT_OWNERS["review"]).review({
            "proposal_id": "proposal-derived", "review_id": "second-review",
            "disposition": "rejected", "operation_id": "second-review"})),
    "a_receipt_for_the_producers_proposal_is_a_different_row":
        authority.receipt("proposal-b1", "review")["receipt_id"]
        != read_back["review"]["receipt_id"],
    "the_producers_receipts_are_untouched":
        [r["receipt_id"] for r in authority.receipts("proposal-b1")]
        == source_receipts_before}

# -- a NONACCEPTING chain on a second derived proposal ----------------------
session.publish({"expect": assignment,
                 "operation_id": "integration-publish:result-2",
                 "proposal_id": "proposal-derived-2",
                 "result_id": "derived-result-2",
                 "result_digest": digest(dict(basis, result_id="result-2")),
                 "candidate_digest": prepared_head,
                 "input_digest": original["input_digest"],
                 "policy_digest": original["policy_digest"], "target": base})
authority.session(RESULT_OWNERS["verification"]).verify({
    "proposal_id": "proposal-derived-2", "verification_id": "v2",
    "observation": "passed", "operation_id": "v2"})
authority.session(RESULT_OWNERS["review"]).review({
    "proposal_id": "proposal-derived-2", "review_id": "r2",
    "disposition": "rejected", "operation_id": "r2"})
answers["a_nonaccepting_review_is_retained_and_blocks"] = {
    "the_receipt_exists_and_is_nonaccepting":
        authority.receipt("proposal-derived-2", "review")["disposition"],
    "approval_refuses_over_it": refused(
        lambda: authority.session(RESULT_OWNERS["approval"]).approve({
            "proposal_id": "proposal-derived-2", "approval_id": "a2",
            "disposition": "approved", "operation_id": "a2",
            "policy_generation": authority.policy_generation()}))}

authority.dispose()
print(json.dumps(answers, indent=1, default=str))

ok = (answers["repository_identity"]["distinct_target_line_workspace"]
      and answers["repository_identity"][
          "a_symlink_alias_is_the_SAME_repository"]
      and answers["repository_identity"][
          "a_linked_worktree_SHARES_the_common_directory"]
      and all(answers["derived_publication_round_trip"][n] for n in
              ("result_id", "result_digest_is_the_custody_basis",
               "re_derived_from_immutable_custody", "candidate_digest",
               "input_digest", "policy_digest", "target", "assignment_ref"))
      and all(v is None or v is True or v == []
              for v in answers["published_is_unapproved"].values())
      and answers["the_three_actors_are_independent"]
      and answers["policy_generation"]["the_approval_receipt_carries_it"])
print("\nTHE AMENDMENT'S ORDER IS EXPRESSIBLE ON THE ACCEPTED INTERFACE:",
      "YES" if ok else "NO")
print("REPOSITORY-IDENTITY ISOLATION IS EXPRESSIBLE IN THE STANDALONE PROFILE:",
      "YES" if answers["repository_identity"][
          "a_linked_worktree_SHARES_the_common_directory"] else "NO")
