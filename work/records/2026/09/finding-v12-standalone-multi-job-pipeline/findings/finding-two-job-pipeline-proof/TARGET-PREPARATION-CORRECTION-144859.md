# W71879 fresh-target preparation correction — tuner144859

Prepared under owner return144855 and review-2026-09-11T13-51-50Z.md.
The correction is ready for independent review. It does not authorize another
model run, repair either failed run or establish A/B integration success.

## Candidate and exact correction

`prepared-144859/candidate-manifest.json` binds 25 new files by hash/size/mode;
SHA-256 `sha256:6b4121c4f36c3b881e4fd2d8edcc09ac358c6c28b5b98b787c1a7f1185aa9b33`.

The candidate contains four Python files, an operator script, two provenance
image documents, two record snapshots, five tasks, seven policies and four
evidence files. The manifest itself is outside its own enumeration. New scripts
are ordinary non-executable files invoked by explicit Python/Bash. The complete
delta from prepared-144415 is in evidence/helper-delta.patch. Every one of the
159 accepted run2 candidate files and the 45-entry provider chain revalidates
unchanged; neither live run1/run2 nor their reviewed packages were edited.

The confirmed target-gid defect is reproduced by a read-only call on run2/target:
`gid 1000, expected workspace gid 1001`. Its root metadata remains unchanged.
This observation is not the unretained original launch error: the first run2
posture failure remains source-inferred and the later existing-root refusal
remains separate parked W144813.

Additional current-source requirements are material to this correction:
`v12/worker/integration_workload.py:_owner_writable` requires owner uid equal to
the fixed runtime uid65532 and owner write on affected files and their parents.
Its preflight maps Git100644 to exact0644. Therefore group1001/mode0664 with
operator ownership would still refuse. The candidate does not relax either
check. It initializes the fresh target to65532:1001 and sets the three existing
changed files to0644 before any submission. Directories remain group writable
and traversable with setgid inheritance; Git metadata is checked separately.

Because the host manager retains its uid1000 and the target belongs to65532,
its child Git environment adds exactly `safe.directory=<future target>` using
GIT_CONFIG_COUNT/KEY_0/VALUE_0. No global configuration or wildcard trust is
written, and container identity/privilege stays unchanged. The worker owns its
own target and uses its unchanged isolated revision reader. Host baseline/final
Git reads now use --no-optional-locks so they do not refresh target metadata
while checking it. This exact-path trust/initial uid/mode setup is explicitly
included in correction review and operator disposition, not hidden as a group-only
change. The operator needs sudo authority for fresh initial chown; no agent
executes that operation.

## Read-only preflight and call sites

`target_posture.py` SHA-256:
`sha256:62edccc553861eed2ed8f05d44ac47b6b38e8e6b86de2dd4994608028d6cfd97`.

The production command fixes uid65532/gid1001. It checks the canonical target,
all Git metadata directories/files, and all five permitted task paths. Directories
require owner/group read/write/traversal and setgid. Existing affected files
require matching uid/gid and exact0644; future additions must be absent and have
compatible parents. Mutable Git metadata requires owner/group read/write;
immutable object/template files need read access. Missing/unreadable metadata,
links, special entries or wrong access refuse. No permission, ACL, ownership,
Git-state or content repair occurs in the preflight.

`deployment.baseline()` calls it before any Git query. Prepare, validate, render
and provision all reach that baseline before their first write. `run.main()`
reaches it before capacity queries, submit or serving; prior read-only freshness
observations remain. The serving subprocess receives only the exact-target Git
trust setting. The run-review gate now also requires target_posture.py in the
reviewed_files bindings, alongside deployment.py and run.py. Ordinary integration
root/posture and worker whole-path authorization checks remain unchanged and
still run; the preparation observation is not a promise against later mutation.

## Focused verification

`test_target_posture.py` is an additive dossier helper test file authorized by
return144855 and the standing campaign test scope. It does not alter existing
Baton tests or their expectations. Ten tests pass on the final candidate:
compatible/read-only fixture, wrong group, wrong owner despite group access,
missing directory setgid, missing root group write, nonwritable mutable Git
metadata, affected-file mode mismatch, preparation refusal before Git/Authority
work, run refusal before submit/engine command, and exact/process-local Git trust.
Python imports/AST and Bash syntax pass. Five task bodies/verification commands
and seven policy behaviors/limits are unchanged, apart from future identities,
root/scope and the current owner-ruling locator.

Positive fixtures use actual managed uid1000/gid1000 as explicit function
parameters; the production CLI offers no uid/gid override and defaults remain
65532/1001. These fixtures are real files and directories, not Git repositories.
They validate the permission predicates and absence of mutation. They are **not**
a successful kernel-access or Git execution test as65532 against a real fresh
host target. The operator script's final fixed-default check must validate the
actual prepared target. Unit-only gate mocks in the pre-submit test never write
a review marker, create a runtime or claim actual acceptance.

Both ten-test runs passed; the second followed the added new-helper review binding.
Retain fixtures /tmp/w71879-target-posture-144859-o0ana123 and
/tmp/w71879-target-posture-144859-5zcydkei. Focused results, read-only run2 refusal,
continuity checks, helper delta and spending live under prepared-144859/evidence/.
No model, container, production Authority or Git repository was created by these
checks. No broad suite or parked hardening matrix was added.

## Exact operator preparation and continuation

After independent correction review and operator disposition, the exact
**Slawomir-only** command is:

```text
/bin/bash /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/operator-prepare.sh
```

Script SHA-256:
`sha256:d5eba75e9ab54ae61c966c398e0be112d711e5c644cb2c5289d1f10e3ffef949`.
It requires the operator already holds gid1001, refuses any existing
/home/sl/.local/state/baton/v12/w71879-run3 root/symlink, verifies original source,
sets umask0002, clones a new source, creates the empty target with
`install -d -g 1001 -m 2775`, clones without hardlinks, and creates the private
bare integration workspace. It initializes the three affected files to0644 and
runs `sudo -- chown -R --no-dereference 65532:1001` on **only that newly created
target**, then verifies baseline and fixed-default posture. This initial fresh
provisioning never runs on run1/run2 or an existing run root. A partial failure
stays intact for disposition; do not rerun the script, delete roots or recursively
repair an existing target. AGENTS reserves Git mutation to Slawomir regardless
of any installed execution rule.

The exact standalone read-only target check is:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/target_posture.py /home/sl/.local/state/baton/v12/w71879-run3/target
```

The future root is still absent now. Its UUID c71879ad000000000000000000000001,
Works/principals/scope/profile/incarnation and storage/credential deliveries are
fresh preparation operands, not permission to spend another attempt. Images,
original commit2fbb2d456638e5706218020aebfa47f0a82c8920/tree3492ba64448ab9d39bde53ee6456ce24e74ece2c,
task behavior and independent review/derived-judgment requirements stay unchanged.
No old credential delivery is copied or credential payload inspected.

After successful operator preparation, tuner can run these separate preparation
commands from /home/sl/src/baton/v12/python, and bind the final rendered operands
in the existing material-delta review:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/deployment.py validate
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/deployment.py render
```

No final configuration or execution-review marker exists for this future package.
An additional model run requires explicit owner authorization after the concrete
corrected package; correction review alone does not grant it. The later exact
host commands, **not authorized for execution now**, use the same cwd/prefix:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/deployment.py provision
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/run.py
```

Supported host execution still needs supplementary1001, declared future-root
writes and ordinary engine access. This candidate asks for no generic grant,
manager/runtime identity substitution, global Git trust, protocol change or live
repair. Future original/derived authorization and both landed/terminal results
remain unproved until an authorized actual run and independent evidence review.

## Costs and deferred work

Run1 223.9077433210041s plus run2 300.8523036100087s totals524.7600469310128s
spent. Prior listed preparation/diagnosis1.2642006099997195s plus this claim's
0.037014676s first test command,0.14364997200027574s static/continuity/live refusal,
0.032825581s final test command and0.0008119190024444833s manifest generation
is1.4785027580024397s, separately from model-run wall time. Test-internal times
are included in their command times, not added twice. All untimed source/metadata/
CLI reads, edits/imports, operator costs and unknown billing remain additional;
no provider reserve transfer or reset of prior failure spending.

Keep1200/240/180/120s limits, including B judges within integration120, existing
resource/storage constraints and no automatic retry. W144813/W144335,
authentication UX, observation/fault-C and broader resilience stay deferred.
Pass this existing Work to baton.feat for correction review, Next baton.ops for
concrete operator disposition. No new planning Work or model-run authorization
is inferred from this handoff.
