# W71879 run7 image and fresh-input preparation — claim 149053

Owner 149049 authorizes this preparation from independently accepted supported-detail
review-2026-09-12T02-08-32Z.md. This candidate is ready for direct independent review.
No model execution is authorized. The existing Docker-copy access boundary from
claim 148686 requires operator execution of the complete build-and-inspect command
below. No denied command was retried or wrapped to bypass that boundary.

**Actual updated image digests remain pending operator build and static inspection.**
There is no candidate-images.json, selected-images.json, execution-review.json,
validation.json, frozen-config or image-build output here yet. offline-images.json
contains historical IDs solely for labelled schema fixtures; rendering cannot use
that filename. This is a reviewable preparation package, not an actual input freeze.
The successful helper will write both real immutable IDs together and retain their
inspection/content evidence; final input review must bind those outputs before use.

Fresh root: /home/sl/.local/state/baton/v12/w71879-run7 (currently absent)
Fresh Authority: c71879b1000000000000000000000001
Fresh scope/profile/incarnation/principals/task/manifest/submission: run7
Created: 2026-09-12T02:23:07.032Z
Original commit: 2fbb2d456638e5706218020aebfa47f0a82c8920
Original tree: 3492ba64448ab9d39bde53ee6456ce24e74ece2c

## Images and installed provider provenance

The accepted COPY-only recipes and ten source/context entries come from
prepared-141676. Only worker/claude_agent.py changes, to accepted SHA256
489399897c3f0ae94f06be9da47adde3f05210fa0ecfd7faad295daf6accfe2a.
Both builds use immutable base
sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4,
with --pull=false --no-cache --network none --platform linux/amd64. No package
installation or download occurs. Each build retains the existing 180s preparation
command timeout; this does not change any proof attempt deadline.

provider-installation.json binds exact 2.1.247 metadata, installer, fallback wrapper
and 250162696-byte native executable from owner 148760/148865 copies, independently
accepted by 148964. Native SHA256:
5fb321bf417ffc5cd4e3f36e7c9c7e029bf47aaa36d5621db979fcc5e6eabe15.
The helper checks those four regular files in BOTH new images, the npm launcher
symlink to the verified native executable, all image-delivered worker source
bytes/modes, immutable base layer ancestry, linux/amd64, 65532:65532 and the existing
provider/integration entrypoints. It rejects credential environment overrides.

Inspection uses two named, never-started, network-none, read-only containers with
no mounts; no provider, model or copied code executes. Both containers and all
partial outputs remain for custody. The helper never retries, deletes or selects
images. Failure prevents writing candidate-images.json; retain the exact output
and return for bounded diagnosis instead of rerunning partial preparation.

## Exact operator preparation commands

After independent review of this candidate, Slawomir executes these separate
commands in order, stopping on any failure. Existing owner 149049 supplies the
bounded preparation authority; Git/ownership operations remain Slawomir's.

Build and statically inspect both images (any cwd):

```text
/usr/bin/python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149053/build_images.py
```

Then prepare the absent run7 root on the host with supplementary gid1001:

```text
/bin/bash /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149053/operator-prepare.sh
```

This preserves the accepted fresh-only checks, clean original run1/source,
no-hardlink clones, bare integration workspace, target 65532:1001 and 0644 file
modes. Historical dirty targets are never baselines. No existing run root is
changed. The managed projected identity cannot establish actual host posture.

With cwd /home/sl/src/baton/v12/python, validate:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149053/deployment.py validate
```

After validation succeeds, from that same cwd, render:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149053/deployment.py render
```

Return actual image-build evidence, both candidate IDs, host posture, validation
and 33 frozen-config files for final binding and independent material-delta review.
Do not invoke deployment.py prepare: the immutable context/tasks/policies/snapshots
are already supplied. Do not provision or invoke run.py under this preparation
handoff. Those remain dependent on genuine final image/input review markers and
separate explicit owner model-run authorization; none is manufactured here.

## Four helpers and unchanged success boundaries

runner-helpers.json binds run.py, deployment.py, target_posture.py and
failure_observation.py. run.py and deployment.py differ from accepted prepared-148870
only in fresh identities/time/ruling metadata. The posture and supported-detail
reader are byte-identical. The runner still requires independent review of all
four helpers and promptly preserves the first definitive required-attempt failure.
No timing, telemetry, containment, custody or lifecycle gate is weakened.

Full A/B tasks, scoped existing-test change and three independent B-derived judges
remain. Integration instruction SHA256 is unchanged:
4b3160e825f6d4f166fc5fc8477f8d85f3190420ba402dcfb780f01df7be9f76.
All integration Git reads still require --no-optional-locks; STATUS still uses the
read-only observing_factory with exact config environment. Held is exceptional;
only actual completed stages can satisfy terminal success.

Preserve 1200s whole/240s implementation/180s original review or derived judge/120s
integration, including B's three judges inside its 120s integration budget. Preserve
2 CPU/2 GiB/512 PIDs per container,20 CPU/20 GiB host capacity,22 GiB available/16 GiB free
and retained-storage stop;512 MiB declared workspace capacity is not a quota.
No ordinary manual transitions, automatic retry, live repair, reserve transfer,
Git mutation by agents or historical root/evidence changes.

## Offline verification and exact test scope

```text
python3 -B /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-149053/verify_offline.py
```

58 tests pass: 54 accepted cases rebased where necessary, plus four new image
preparation cases. Real schemas/public temporary Authority bootstrap, observer,
report/prompt/Git witness, first-failure and supported-detail fixtures are covered.
No real engine/model/credential/runtime/store or host validation is represented.
Temporary public bootstrap uses its public API, never raw store rows. Runtime and
Git-read test fixtures are retained and explicitly labelled offline.
Successful retained suite: /tmp/w71879-149053-offline-verification-57wa43rd.
First suite 57/58 passed: a new textual assertion expected bare helper filenames
where the accepted guard uses HERE/path expressions. Only that new assertion was
corrected; the failed log and 0.3687735180137679s remain in owning evidence.
Final suite process wall 0.3740565679909196s. Bash syntax, Python AST compilation and
git diff --check pass. Product adapter/tests remain exactly as accepted by 148964.

Changed copied tests: test_manifest_timestamp.py, test_report_instructions.py and
test_observed_status.py update run identity/time and explicitly use offline-images;
test_run7_preparation.py rebases four existing preparation cases from run6 to run7.
test_early_failure.py keeps genuine historical run6 detection with explicit old
UUID/Works and relabels only an explicit synthetic copy when exercising the fresh
runner. test_stats_observation.py and test_provider_detail.py are byte-identical.
New test_image_preparation.py checks context continuity, static file/type/mode/hash
rejection, launcher target and exact installation/four-helper binding. W71830
standing test-change authority applies. No old package or test file was edited.

Owning evidence/image-preparation-149053 retains exact copy deltas, verification
logs/commands, prior76/43/568-file manifest verification,45 provider-chain entries,
seven composition/observer bindings, current baseline/image read observations and
spending. All eleven copied context files preserve prior modes; source content
changes only for the accepted adapter. record-snapshot contains current owner scope;
copied historical evidence remains labelled by its original claim/run.

Cumulative listed preparation/diagnosis: 39.886439952919716s.
Six failed runtime walls:1341.1107609820174s. Untimed reads/edits/static work, prior
failed commands and host/operator/billing uncertainty remain additional; no inner
suite/tool-wall double counting. Actual A settlement, B-derived judgments/import,
causal merged observations and both terminal Jobs remain unproved. Run5 exact writer/
coordinator-entry uncertainty and run6 discarded cause remain. W144335/W144813/
W136578/W129838, fault-C/H7 and general resilience remain deferred.
