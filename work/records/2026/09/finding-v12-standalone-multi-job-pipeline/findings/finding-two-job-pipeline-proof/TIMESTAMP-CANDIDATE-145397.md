# Exact run4 timestamp correction — tuner145397

Owner145370 and review-2026-09-11T15-25-58Z.md authorize this bounded correction.
prepared-145397 is ready for independent review, with20 passing offline tests.
The existing prepared, unsubmitted run4 operands remain in place. No additional
model attempt is authorized or executed.

## Bound change and provenance

prepared-145397/candidate-manifest.json binds27 files by SHA256, size and mode:
`sha256:46ac9d39fdb0e49728835696f04efd2d784f606b13982789b4406443aba4ad78`.

The only helper change from prepared-145261 is deployment.CREATED:
`2026-09-11T15:06:04Z` becomes `2026-09-11T15:06:04.000Z`.
The instant is preserved. Corrected deployment.py digest:
`sha256:9895f6c29b6fe3a82a8740d400e16a2bdda85d996e2a025d54bf2d4ff65707cf`.

The package copies21 required helper/input files;20 are byte-identical and only
deployment.py has that one-line change. It adds test_manifest_timestamp.py and
five current evidence files. evidence/provenance.json enumerates each copied
source/candidate digest; timestamp-delta.patch shows the entire helper change.
The old25-file candidate and45 provider-chain entries still match their accepted
bindings. Prior evidence, tests and immutable packages are untouched.

run.py, target_posture.py and test_stats_observation.py are byte-identical to
prepared-145261. Task/policy/image documents and record snapshots are unchanged.
The new directory changes the helpers' naturally resolved HERE/config paths;
run4 UUID c71879ae000000000000000000000001, root, Works/principals/scopes/profile,
original base/tree, task behavior and every budget remain unchanged. No replacement
namespace or new Git/ownership operation is introduced. Copied operator-prepare.sh
is historical dependency evidence and must **not** run again.

## Actual schema regression evidence

New additive path: prepared-145397/test_manifest_timestamp.py, authorized by
owner145370 and standing W71830 test scope. No existing assertions were changed.
Its tests exercise actual deployment.documents/input_manifest and frozen
check_manifest_structure, without mocking the validator:

- The candidate constant emits33 document files, including all six valid input
  manifests with the exact corrected timestamp.
- Replacing the timestamp with the original value in each manifest and recomputing
  its digest still produces the actual created_at schema-pattern refusal.
- A test-local old constant also fails through the real documents constructor;
  no stage-execution document is emitted on that path.

All three tests and the17 copied stats tests pass. Stats gaps/flushes, watchdog
and required-observation/resource/deadline/terminal guards remain accepted.
Evidence: evidence/verification.json and verification.txt. Fixtures are retained:
/tmp/w71879-145397-schema-fixtures-u94skijz and
/tmp/w71879-145261-unit-runner-isendlwe. Synthetic constructor facts and emitted
/tmp documents are explicitly test data, never public Authority observations,
actual host validation or final run inputs. No Authority/model/engine/Git operation
or real review marker was created by these tests.

For independent rerun without overwriting candidate evidence, use cwd
/home/sl/src/baton/v12/python and:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 -m unittest discover -s /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145397 -p 'test_*.py' -v
```

## Exact corrected host continuation

Pass W71879 to baton.feat for independent correction review, Next baton.ops.
After that review, execute these two commands separately on the host, with cwd
`/home/sl/src/baton/v12/python`. Validate first:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145397/deployment.py validate
```

Only after validate succeeds, render:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145397/deployment.py render
```

Both retain the real host posture/baseline checks. The managed65534 projection
cannot stand in for host65532:1001; no schema/posture bypass or new generic grant
is proposed. No actual corrected host validation was attempted in this claim.
The new helper intentionally retains its existing temporary-directory prefix;
a new validation creates a distinct temporary path and preserves failed
/tmp/w71879-145261-validation-00nb1okq. Do not reuse fixture outputs as validation.

Current run4 contains only source, target and integration-workspace; both old and
new candidate validation.json/frozen-config/acceptance markers remain absent.
Do not rerun operator-prepare.sh, change roots/ownership, delete partial evidence
or invent another namespace. After successful host outputs, tuner binds actual
rendered files for the existing final material-delta review and operator execution
disposition. No additional planning prerequisite is needed.

Later commands from the same cwd remain **held**, pending actual final inputs,
genuine independent review/markers, suitable host access and explicit owner
authorization of another model attempt:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145397/deployment.py provision
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145397/run.py
```

No further attempt is authorized now. Actual original reviews, A integration,
B independent derived judgments/coordinator import, both landed changes and both
terminal Jobs remain outstanding. Keep the absence of a B model integration
runtime explicit where the accepted coordinator performs the import.

## Preserved costs and limits

The three failed runtime walls remain560.1007706070232s. Prior listed preparation/
diagnosis2.670276407029118s plus tests0.19202788200345822s, provenance/static
0.009140584006672725s and manifest generation0.0009651449945522472s totals
2.872410018033801s. Internal timing is counted once; untimed reads/edits/CLI, failed host
validate/render/operator time and billing uncertainty remain additional. No fourth
model run or reserve transfer is attributed to this packaging error.

Preserve1200/240/180/120s including B judges within integration120;2CPU/2GiB/512PID
runtime caps;20CPU/20GiB host capacity,22GiB available memory,16GiB free-storage
preflight/retained-storage stop; declared512MiB capacity is not a quota. No retry,
live repair, deadline increase, schema relaxation or broader scope. W144813/
W144335/authentication UX/observation/fault-C/stronger hardening remain deferred.
