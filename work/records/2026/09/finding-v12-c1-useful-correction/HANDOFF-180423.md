# W180245 C1 candidate — independent review requested

baton.tuner claim180423, owner decisions180294/180421. Pass baton.feat, next
baton.ops. Implementation and author verification are complete; C1 acceptance
and C2 shared-file release remain independent decisions. This handoff supersedes
HANDOFF-180298.md's pending worker selection and incomplete C1 status; its
observations, failed runs and partial snapshots remain intact.

## Behavior and selected source corrections

The real deterministic C1 path produces multiplier2 code and executes its
verifier, receives an actual independent changes-requested review, then restores
the same context line into a fresh implementation attempt. The revised
multiplier3 code and verifier execute, receive an actual accepted review, and
pass through managed preparation, three independent judgments, apply, import,
target publication receipt, final collection and capacity release. Run10 ends
in23 logical ticks with the root ended and revised target bytes recorded.

`integration/reconciliation.py::adopt_prepared_candidate` retains the original
first-nonzero aggregate while deciding eligibility from a complete measured
combined/base/isolated sequence. Combined0/base1/isolated0 and all-zero are
eligible; combined/isolated failure and incomplete/unmeasured sequences remain
blocked. The actual preparation report remains aggregate1 in the C1 evidence.
Identity, source, retained custody and replay owners remain in the real path.

The owner180421 exception changes only `baton_worker.py::context_declaration`
and `handle` relative to accepted B: context-free integration may consume the
exact shared optional reserved declaration, and must report it missing while
producing no receipt path. Delivered context, including null/malformed members
and the contextual launch schema, still refuses. Declaration constraints and
existing implementation/review context rules remain enforced. No manager
declaration bypass or relabelled integration role is used.

## Exact candidate and provenance

`CANDIDATE-180423.json` SHA256
`2e7107ecbfc133374e1811e33e99e3764924c20f90ceb22ab71683a00d834499`
binds seven files, exact baseline/current hashes and modes, immutable candidate
snapshots, unchanged selected files and read-only dependencies. The baseline
combines BASE-180298's original six paths with BASE-180423's newly selected
worker/test paths. `candidate-180423.patch` reconstructs every candidate byte
from those exact bases using patch with zero fuzz. This is the C1 delta;
repository HEAD also contains unrelated and already accepted work.

| Repository path | Candidate SHA256 |
| --- | --- |
| v12/python/src/baton_v12/integration/reconciliation.py | bc3bf48d5c2fcf8edce7de7171fae86b3871fc1c6d7a3879f26d49b9202e1d2e |
| v12/python/tests/integration/test_managed_storage.py | faf677c2fbf5c8e928f460f8db6853bc11f3a66e6ed78f5f33faefe68c799a81 |
| v12/python/tests/tools/correction_restart_trace.py | b40057b231c0c102a2b67790c02ed2f506169caa364a6763c28dd4064684422f |
| v12/python/tests/tools/test_correction_restart.py | a9a861f732331b5b4dae839a028d4b27a0316da2599f5f9f610d42973803cfae |
| v12/python/tests/tools/test_managed_apply.py | 6af27ca099f480a6a4552c8e834c6a6e58c8ffa52d502f1770f9a3963e515c51 |
| v12/python/tests/tools/test_single_worker.py | d0503d09efc0ae28653805808348c352e3caa078df10e0a1d418c91eeb1df61c |
| v12/worker/baton_worker.py | 0b5a94bc86b22ef88a0b95ae9ae257ba33bef33841d11876c91a744d7d8bd0c7 |

Candidate snapshots use0444 for evidence custody only; existing repository modes
are unchanged and owner-writable. The candidate is already in this working
tree. No Git index, history or branch operation was performed. Accepted A/B
inputs match their recorded hashes except the explicitly selected worker/test
exceptions. test_managed_preparation.py and test_claude_context.py are unchanged.

## Tests, oracle and scope of evidence

`EVIDENCE-180423.json` SHA256
`7ebf7dcf65b6e2242cb8ced6d200da7f6f94486c259b6e9f6f92d5a7a3932659`
binds the candidate, actual exports, all eleven run receipts/logs, supervisor,
Python/dependency environment, prior evidence and newest independent triage.
Final runs9/10/11 all match the packaged source bytes:

- Run9: UsefulCorrectionInvalidEvidence,5 tests and13 labelled synthetic
  corruptions rejected by the exported-record validator. Cases cover unchanged
  correction, absent/unexecuted/wrong-byte verifier, original target,
  absent/forged/misbound verdict and reviewer producer-context/writable-line
  exposure. The original actual observation validates before and after mutations.
- Run10: UsefulCorrection,2 tests. The real C1 scenario validates, and all18
  unchanged predecessor schedule artifacts validate without executing schedules.
- Run11:36 focused regressions:17 PreparedEligibilityUsesCandidateMeasurements,
  2 OptionalIntegrationContextDeclaration,3 ContextFreeIntegrationReceiptBoundary,
  and14 unchanged ServingBinding/WorkerInvocation/RestoredCorrectionBoundary.

The existing storage/single-worker/managed-apply files gain focused tests without
weakening existing expectations. The two shared draft files replace the
placeholder C1 oracle with real receipt extraction and independent validation,
and add the selected positive/negative acceptance. Existing context tests remain
unchanged. These changes are within the owner-selected test paths and standing
test authority; independent review must assess the actual expectations.

The companion validator consumes exported records only. It rederives code and
verifier digests, checks same-line/fresh-attempt receipt identities, actual
verifier execution, checkpoint/verdict correlation, reviewer isolation,
managed candidate/target/judgment/publication/final receipts, and context-free
apply absence. It is a consistency oracle; the supervised export and exact
artifact hashes supply provenance. Synthetic mutations are never owner receipts.

Reviewer isolation clarification: the accepted source mount uses the fenced
checkpoint checkout read-only at /input/source. Its host path can be the former
producer checkout. The extractor and validator require the exact frozen head,
read-only access and no producer private-context mount; rejecting every host-path
overlap would incorrectly reject this accepted configuration. Simulated OCI
mount evidence does not claim physical container isolation qualification.

## Preserved development evidence and cleanup

All eleven runs are retained. Runs1/7 passed exploratory C1 before the final
oracle; run4 passed new worker guards. Run2 exposed test setup omissions (manager
integration role and worker request identity fields). Run3 exposed an overly
strict read-only checkout assertion. Runs5/6 exposed final-launch extraction
mistakes; the collector now retains the actual launch at the engine seam before
owner disposal. Run8 caught explicit readonly string normalization in mount
evidence. These were corrected in the selected tests/harness; final runs9–11
passed. Earlier claim180298's source blocker and all predecessor failures remain.

Every run stayed within its180s supervisor, TERM5/KILL5 cleanup bounds and100
scenario ticks. All eleven receipts report subreaping, no timeout, positive
process-group absence and stable source hashes during execution. The packaging
audit reconstructs candidate bytes in a temporary directory and cleans its own
directory; it executes no test or provider.

Measured author verification this claim32.104145374090876s; cumulative author
211.3880788211536s including prior179.28393344706274s. Prior reviewer
93.48170357503113s remains separate. No cost is discarded or inferred.

Evidence uses a deterministic provider and simulated OCI boundary while running
real Python worker/provider children, Git/verifiers and affected coordination,
workspace, managed preparation/apply/import and final-result owners. No live
provider, actual OCI engine, image work, broad suite, predecessor schedule rerun,
DEPLOYMENT.md change or production qualification occurred. The retained reopen
helper is uncalled; no C2 counting/reopen acceptance is claimed.

## Handoff and remaining ownership

Read FINDING.md, PLAN.md, PROGRESS.md, this handoff and the independent triage
`review-2026-09-15T18-48-11Z.md`. Review the exact candidate and final evidence,
then pass to baton.ops for acceptance. Tuner releases all seven paths for that
review and will make no further writes after passing. The two shared files are
named and hashed above; release to C2 W180252 requires C1 independent acceptance
and an explicit accepted-hash handoff. C2 remains blocked. No external release.
