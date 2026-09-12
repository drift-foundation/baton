# W71879 authorized run2 preparation — tuner144415

Owner return144411 authorizes one fresh run2 after the host login/pong in M144306,
accepting unresolved run1 provider causality. The ruling is pinned in FINDING and
current PLAN. Run1 remains failed and preserved. Its 223.9077433210041 seconds,
unknown provider billing and all preparation/diagnostic uncertainty stay spent.
No further automatic retry, repair, rebuild, timeout increase or hardening gate.

## Prepared inputs and exact delta

`prepared-144415/preparation-manifest.json` binds 25 files by hash/size/mode;
manifest SHA-256:
`sha256:7ecaec5de234b28e92201e183f0732d3f3e7592f530b0562726d8d2dbdc6ef58`.
They are two adapted execution helpers, the operator-only Git preparation script,
five tasks, seven policies, two current record snapshots, reused image IDs/context
manifest and six evidence files. No accepted historical package is edited.
The manifest itself is an additional file, outside its own enumeration.

`evidence/helper-delta.patch` shows the complete helper changes from accepted
prepared141676: w71879-run1 becomes w71879-run2; the Authority UUID changes from
c71879ab000000000000000000000001 to c71879ac000000000000000000000001;
the declaration timestamp and owner-ruling locator change; temporary validation
paths identify this claim. All operation logic, limits and task behavior remain.
The runner changes only its two incarnation literals; deployment constants supply
the other fresh identities. Job-local names job-a/job-b and logical target name
w71879-target remain local to the new Authority/store; they do not reuse run1
state. Work IDs become c71879ac-W1 through W5, scope/profile/principals and all
mutable run roots become run2. Participant role names stay consistent within the
new Authority. Each normal launch gets a new run2 credential delivery home.

The unchanged configured operator-file/w64268-run1 reference still resolves in
registry metadata to /home/sl/.claude/.credentials.json. The reference's historical
name does not mean reusing run1 attempt credentials. The owner reports the host
source was refreshed; the ordinary adapter will deliver it into fresh homes.
No credential payload was read, copied or exposed during preparation; no claim
of renewed authentication inside an old attempt is made.

Both accepted image IDs remain:

- provider: sha256:26cdfe7df693d3cfad0190e879e93ba9f3fea2086ecb5c7f1f4c2fe598aced99
- integration: sha256:8e84757c898b15b98fce42ca2d5a3a4ba07e44c0c744978870bdf36a4aa2cdb2

All 79 files of the prior accepted candidate and its 45-entry provider chain
revalidate unchanged. All five task instruction bodies and verification commands
match run1 exactly; only task IDs change. Seven policies differ only in run-root,
scope and the new owner-ruling locator. Python AST and shell syntax checks pass.
See preparation.json, static-validation.json and command-grants.json under the new
evidence directory. No image build, provider probe, product source/test change,
Git mutation, production Authority or submission was performed by this claim.

## Required operator action before final rendering

Run2 root does not exist. The ordinary held-configuration validator nominates a
real source directory, so `deployment.py validate` stopped with ContractRefusal
when `/home/sl/.local/state/baton/v12/w71879-run2/source` was absent. That is an
honest unmet filesystem prerequisite, not a provider defect or authorization to
substitute another run's live source in the executable configuration. Complete
trace: evidence/validation-source-absent.json. The public temporary bootstrap and
partial document output remain at /tmp/w71879-144415-validation-yywyz7p8; no
production state was created. Do not delete or repair that diagnostic directory.
No final frozen configuration, successful validation.json, selected-images.json
or execution-review.json has been fabricated for run2.

The exact next **operator-only** command is:

```text
/bin/bash /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144415/operator-prepare.sh
```

The script is readable non-executable repository evidence, invoked explicitly by
Bash. It refuses an existing run2 root, checks run1/source is clean on main at
commit2fbb2d456638e5706218020aebfa47f0a82c8920/tree3492ba64448ab9d39bde53ee6456ce24e74ece2c,
then creates a private run2 root, two clones with independent object files and a
bare integration workspace. Source and target are verified at that same baseline;
no commit, branch rewrite, run1 change, credential copy, Authority or submission.
Any partial failure is retained and reported, not automatically removed or retried.
This Git action remains Slawomir's under AGENTS; do not grant it to an agent.

After operator success, return the same Work to baton.tune. Tuner first validates
actual clone identities/payload and bare workspace, then runs these two separate
preparation commands, each from `/home/sl/src/baton/v12/python`:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144415/deployment.py validate
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144415/deployment.py render
```

Validation uses a fresh temporary public Authority; rendering freezes the actual
run2 configuration against the reused images. Do not call prepare or build_images:
reviewed contexts/images are already available. Bind every final executable input
and both helpers in the existing baton.feat material-delta review. The run1 review
remains image/task/source provenance and does not attest run2 configuration hashes.
Only genuine run2 acceptance may supply run2 execution-review.json. No new planning
Work, speculative product correction or additional robustness prerequisite.

## Exact later host commands, held until final review

Once the changed inputs are independently accepted and genuine selection/review
markers materialized, the two separate commands are, from the same cwd:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144415/deployment.py provision
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144415/run.py
```

Neither exact command matches the installed default.rules/baton.rules grants.
The operator may execute after acceptance, or supply these exact managed host
execution boundaries with supplementary gid1001, run2-root access and ordinary
engine access. No generic Python/Docker grant or host restart is proposed.
Provision creates fresh run2 public Authority state/roots, never claims or reports;
run submits once and serves ordinary owners. Run1 stores/runtimes/credentials are
never a provisioning or submission target. Preserve private original bases and
real original reviews, A direct integration, B merged-candidate causal checks and
actual independent verification/review/approval judgments. B's model integration
runtime remains honestly absent where the coordinator performs the accepted import.
Independent final assessment still owes both landed changes and both terminal Jobs,
actual original/derived authorization, source/target cleanliness and final tests.

Limits stay 1200 seconds wall, 240 implementation, 180 original review/judge and
120 integration including B judges. Resource thresholds, storage observation,
exceptional containment of this Authority's own runtimes and all deferrals remain.
The fixed provider-diverse label is not a new model/vendor-diversity claim.

## Spending and handoff

Run1 wall cost remains 223.9077433210041 seconds, separately from listed preparation
costs. New measured checks are 0.007775528996717185 seconds for original package/
baseline continuity, 0.045287253 for the failed source-nomination validation command,
0.13649385400640313 for static helper/task/policy checks, and 0.0006052349926903844
for manifest generation. Prior listed preparation 0.8228611680074099 plus these is
1.0130230390032207 seconds; this is not a complete wall-time claim. All prior and
current untimed reads/edits/diagnostics, provider billing uncertainty and temporary
paths are retained. No run2 model/submission allocation or provider reserve was used.

Return the incomplete freeze through baton.bug with Next baton.ops for this exact
operator Git prerequisite, then tuner resumes validation/render and the existing
material-delta review. This is an executable operational handoff, not a request
for a new product decision or permission to retry run1. Owner's one-run2 authority
persists; it does not need to be asked again.

The concurrently recorded UX-DECISION-2026-09-11T12-44-51Z.md was read before
handoff. Its actionable authentication-failure UX requirement remains explicitly
deferred and does not change this package, authorize a probe/source change or
gate run2. It does not retroactively establish run1 provider causality.
