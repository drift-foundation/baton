"""Write EVIDENCE-199021.json. A record-writing helper, nothing else."""
import hashlib
import json
from pathlib import Path

HERE = Path("/home/sl/src/baton/work/records/2026/09/"
            "finding-v12-worker-launch-version-mismatch")
P = HERE / "instance-199021"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


package = {str(p.relative_to(P)): sha(p)
           for p in sorted(P.rglob("*")) if p.is_file()
           and "__pycache__" not in str(p)}

found = {
 "schema": "baton.w197661.evidence/1",
 "claim": 199021,
 "work": "2b077949-W197661",
 "authority": "owner seq198635, continued under review-2026-09-18T01-21-09Z.md; "
              "the labelled synthetic credential fixture needs no further owner "
              "gate per that review",
 "corrects": {
  "R1": "the credential-empty refusal is recorded as a DEPLOYMENT LIMITATION and "
        "worked around with a private disposable synthetic non-bearer source "
        "this run wrote; no real credential file was read or reused and no "
        "authentication coverage is claimed",
  "R2": "ONE input manifest per Job, shared by all three stage workers; the real "
        "_SingleWorker._matches now accepts implementation, review AND "
        "integration. The product equality check is untouched and no seal is "
        "spoofed.",
  "R3": "every placeholder replaced by a measured identity, and main() fails "
        "closed"},
 "package": package,
 "validators": {
  "all_accepted": True,
  "named": ["check_manifest_structure", "bootstrap.held",
            "stage_execution.held_configuration", "bootstrap.validated",
            "job_manager.documents.owned_submission",
            "stage_execution.held_configuration (over the written files)"]},
 "lifecycle_reached": {
  "capacity_bootstrapped": {
   "how": "the installed `baton-v12-stack bootstrap --inputs ...` WITHOUT "
          "--destination, which is prepare-only and is what a repeated "
          "bootstrap supplying workers is",
   "the_refusal_that_taught_it": "with --destination it refuses: 'there is "
                                 "already a runtime at <dest>/distro; nothing "
                                 "here upgrades a deployment in place'",
   "identity": "reused from this root's record (b0657dfa...)",
   "routes": ["impl -> baton.w197661-author",
              "rview -> baton.w197661-reviewer",
              "integration -> baton.w197661-integrator"],
   "work_created": "b0657dfa-W1 on impl",
   "grants": "approve/review/verify/integrate in its own scope",
   "capacity": "1 Job, one worker per role, schema "
               "baton.v12.stage-execution-deployment/1",
   "seconds": 0.250},
  "job_submitted": {"through": "the installed `manager submit`",
                    "returncode": 0,
                    "submission_id": "w197661-lifecycle-199021",
                    "seconds": 0.268},
  "scheduler_started": {"through": "the installed `start`", "returncode": 0,
                        "manager_pid": 525208, "publisher_pid": 525209,
                        "seconds": 0.499},
  "candidate_collection": {
   "state": "THE CONTAINER RAN AND THE WORKER FINISHED; the stage did not "
            "conclude",
   "container": "d10ed9224639 from the labelled fixture image, Exited (0)",
   "exchange": "describe and work answered; terminal disposition=completed "
               "ending=answered",
   "worker_result": "a baton.worker-manifest/completion with three present "
                    "outputs and measured content manifests",
   "output_axis": "reached `sealed`, so intake and custody DID complete"},
  "stage_state": "answering, and it will never leave it -- see the finding",
  "independent_review": "NOT REACHED; blocked behind the implementation stage",
  "report_and_hold": "NOT REACHED; the Job's terminal_policy is "
                     "report-and-hold and the projection confirms it, but no "
                     "stage ended"},
 "OPERATIONAL_FINDING": {
  "what": "the implementation ending cannot re-enter once intake has sealed "
          "the output",
  "measured": "two independent `serve --once` reconciles, 72 seconds apart, "
              "each owed `conclude` for the attempt and each DEFERRED it with "
              "the identical refusal refused/precondition: \"attempt '...' "
              "output is sealed; custody is taken of a FROZEN result, and no "
              "other state is one\" (intake.py::_collectable)",
  "why_it_matters": "review_driver.end_implementation documents that EVERY "
                    "step replays and that a process death between any two "
                    "steps re-enters and finishes. Step 5 does not: "
                    "`_collectable` refuses an output that is already "
                    "`sealed`, which is the state its own success leaves "
                    "behind. So an ending that got past intake and failed "
                    "afterwards can never be completed.",
  "the_observability_half": "the operator surface shows ONLY `answering`. The "
                            "stage's receipts are admit and claim and nothing "
                            "else; `status` reports a healthy manager, a fresh "
                            "snapshot and one observed Job. The deferral "
                            "exists solely in the reconcile report, which the "
                            "serving loop does not persist. That is the same "
                            "shape as the reported incident: a runtime that "
                            "finished, a manager that looks well, and nothing "
                            "that says why.",
  "related_comment": "end_implementation's own W124784 note describes this "
                     "outcome exactly -- \"the stage stays `answering` and "
                     "asks again forever\" -- for a DIFFERENT cut point, and "
                     "added `_cleaning_implementation` for that one. This cut "
                     "point has no such branch.",
  "NOT_DIAGNOSED_HERE": "which step after intake failed the FIRST time is not "
                        "established. The fixture's scripted agent writes "
                        "result_metadata {} for its git-change-proposal "
                        "output, so it carries no baton.git-proposal/1 claim "
                        "and publication could not succeed -- that is a "
                        "FIXTURE GAP and a plausible cause, not a measured "
                        "one. No product change is proposed on it."},
 "preserved": {
  "the_unresolved_attempt": "attempt-432eb7b77502fbb65e041e5400c54464ae4735374"
                            "9dc5fa9408acb6f617c7af9 and its container are "
                            "RETAINED, not disposed of: the ending never "
                            "authorized cleanup and removing it would destroy "
                            "the evidence of an unfinished attempt",
  "processes": "the manager and publisher this claim started are STOPPED "
               "through the installed `stop`; no process of this claim runs",
  "earlier_packets": "instance-198871 (compose.py, compose_chain.py and every "
                     "output), instance-198750, packet-198640 and the "
                     "corrected-* packages are untouched",
  "production": "the stopped production instance "
                "/home/sl/baton-v12-instance-2026-09-17T20-29-21Z was not read "
                "from, written to, started or changed"},
 "verification": {
  "test_composition": {"checks": 27, "seconds": 0.303,
                       "clean_under": "-W error::ResourceWarning"},
  "verify_lifecycle": {"checks": 33, "all_true": True, "seconds": 0.022},
  "fail_closed_probes": {
   "composer": "six cases drive a refusal at each validator and assert rc=1 "
               "plus INCOMPLETE on stderr; one asserts that a refused seal "
               "stops everything downstream",
   "verifier": "an injected missing status.json makes the run record an "
               "explicit failed check and return 1 rather than raising"}},
 "not_done_this_claim": [
  "the fixture agent composes no baton.git-proposal/1 claim, so no candidate "
  "can be published",
  "independent review and report-and-hold are unreached",
  "the deferred-conclude finding is measured but not diagnosed to its first "
  "failing step",
  "no cleanup or disposal of the disposable instance, deliberately: it holds "
  "the unresolved attempt"],
 "no": ["live model", "production restart, recovery or resubmission",
        "credential harvesting", "public log publication",
        "version-control mutation", "direct store read or write",
        "new image build"]}

(HERE / "EVIDENCE-199021.json").write_text(
    json.dumps(found, indent=2, sort_keys=True) + "\n")
print(sha(HERE / "EVIDENCE-199021.json"))
