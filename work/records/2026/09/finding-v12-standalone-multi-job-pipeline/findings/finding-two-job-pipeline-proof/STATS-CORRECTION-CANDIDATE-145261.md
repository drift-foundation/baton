# W71879 bounded stats correction — tuner145261

Owner145258 accepts STATS-OBSERVATION-CORRECTION-145165.md. The new immutable
candidate is complete for independent review, with17 passing offline tests.
It does not authorize another model attempt or alter any failed run.

## Candidate and behavior

prepared-145261/candidate-manifest.json binds25 files by SHA256, size and mode:
`sha256:7a3987abd1703a0de20db1c46f7d995d65c3d8182fafd53295c49f13e8f18b5c`.

| Artifact | SHA256 |
| --- | --- |
| run.py | sha256:c597468148a15ef4873199d3132b453c26229d6b2c1a9654bc361b578da7fd8e |
| deployment.py | sha256:5fae01e86d4649827fbe3a3a6d5f7a1c88219c0333e8590ee2805181dbde1f97 |
| target_posture.py | sha256:62edccc553861eed2ed8f05d44ac47b6b38e8e6b86de2dd4994608028d6cfd97 |
| operator-prepare.sh | sha256:5fb89519f5355ec2adaa3c08a4ac3dd4aef3195240c70930630b0f4ccacbbf6a |
| test_stats_observation.py | sha256:1faa08e9f5c726802a81353edcf73097be6d24311c2e0fecbfdc53be129b2819 |

The package contains four Python files and one operator script, two image
provenance documents, two record snapshots, five tasks, seven policies and four
evidence files. The manifest is outside its own enumeration. These are ordinary
non-executable files invoked with explicit interpreters. The complete delta from
prepared-144859 is evidence/helper-delta.patch. All229 prior candidate files and
230 actual run3 execution bindings retain their accepted hashes/sizes/modes;
all45 provider-chain entries match. Product protocol/application/image/task
behavior remains unchanged. No submitted root or previous candidate was edited.

The only runner behavior change is stats telemetry and its evidence bookkeeping.
`stats_observation` makes at most one docker stats call per sampling iteration,
using exactly that iteration's inspected runtime IDs and the existing10-second
subprocess timeout. It does not retry or re-arm any timer. Nonzero return
(including EOF), requested empty/whitespace output and subprocess.TimeoutExpired
produce `unavailable`. No requested IDs produces `not-requested` without calling
Docker. A zero return with nonempty output produces `available` command output;
it does not certify complete per-container utilization coverage or lifecycle.

Each sample now stores docker_stats as a structured object, replacing only the
new runner's previous string field. It includes state, requested IDs, UTC start/
end, monotonic duration, exit code or typed error, and stdout/stderr with original
character counts and truncation flags. Stdout is bounded to65536 characters,
stderr to8192. Timeout byte output is decoded as UTF-8 with replacement; this is
retained text evidence, not a promise of byte-exact undecodable output custody.
Partial nonzero/timeout text remains evidence, never fabricated measurements.
No stale/zero/default metrics substitute for a gap. Earlier sample files retain
their original representation and are not rewritten.

Unavailable stats returns to the ordinary sampling loop; the same iteration's
claims, public status, runtime rows/caps and retained-byte observation are written
and flushed. Final run-result.json adds stats_observations state counts, gaps
with exact samples.jsonl line locators/IDs/reasons, and truncated sample locators.
Its coverage description explicitly limits the record to sampled command output.
A gap is not proof of completion, resource use or successful authorization.

Only subprocess.TimeoutExpired is caught at the telemetry boundary. Built-in
watchdog TimeoutError, missing executable and other programming errors propagate
to existing fatal containment. The strict general command helper, Docker ps/
inspect/Authority-label checks, storage scan and serving containment functions
are byte-equivalent ASTs. Main keeps the existing host capacity check, enforced
engine caps, required owner/status/timestamp checks,16GiB stop,1200/240/180/120
absolute deadlines and both-terminal/live-runtime/final verification/cleanliness
conditions. Stats itself never enforced caps. No deadline, budget, claim, source
base or acceptance condition is reset, relaxed or repaired by this correction.

## Offline verification

The only test path added is prepared-145261/test_stats_observation.py, within
owner145258 focused scope and standing W71830 authority. No existing test was
changed. All17 cases pass: success/raw text/IDs/timing; EOF/partial output;
requested empty output; no IDs; bounded truncation; subprocess timeout text;
watchdog/engine/programming errors; strict inspect/label/general command failures;
EOF and timeout continuing through the actual main loop; independently reading
the flushed first sample during the next iteration; actual registered watchdog
handler causing containment; status/inspect/storage and host capacity refusal;
missing claim timestamp and expired active claim; incomplete Jobs remaining
incomplete; and final verification failure remaining fatal.

The loop fixture confirms only one stats call for the observed ID set and the
unchanged decreasing wall-timer schedule. Engine, process, Authority and clock
answers are mocked inside unit tests; all written files are retained UNIT fixture
evidence under /tmp/w71879-145261-unit-runner-4f1gug3v. No real review marker,
Docker, model, Git repository or live Authority is used. This validates runner
control flow, not a real destruction race or a successful standalone pipeline.
The original EOF cause remains plausible/unconfirmed as recorded by review145165.

Python AST, Bash syntax, five task and seven policy behavior comparisons and
prior-package/provider continuity pass. No broad monitoring suite is introduced.
For independent rerun without overwriting immutable focused-tests.json, use cwd
/home/sl/src/baton/v12/python and:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 -m unittest discover -s /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145261 -p test_stats_observation.py -v
```

## Separately enumerated fresh packaging operands

The old run3 root is submitted evidence and cannot be reused. This candidate
therefore mechanically names the absent /home/sl/.local/state/baton/v12/w71879-run4,
UUID c71879ae000000000000000000000001, matching W1/W2 A/B and W3/W4/W5 judge Works,
run4 principals/scope/profile/incarnation, current declaration/ruling and record
snapshots. Five task behaviors, seven policy limits, accepted image pair, original
commit2fbb2d456638e5706218020aebfa47f0a82c8920/tree3492ba64448ab9d39bde53ee6456ce24e74ece2c,
credential source and genuine original/derived judgment requirements are unchanged.
No new source/target/store/credentials or final config was created by this claim.
No selected-images or execution-review marker exists for this candidate.

Deployment and operator preparation logic are reused with identity/path changes
only; target_posture.py is byte-identical to the independently accepted helper.
Real host65532:1001 ownership, affected0644 modes, group/setgid/umask0002 and
process-local exact-target Git trust still apply. The managed ID projection
limitation remains disclosed; no reinterpretation or workaround is introduced.

## Exact operator continuation for disposition

Pass existing W71879 to baton.feat for independent correction review, Next baton.ops.
Owner receives this concrete candidate and the commands below. After accepted
correction and owner disposition, Slawomir alone may initialize the fresh Git
operands (never run this on an existing root):

```text
/bin/bash /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145261/operator-prepare.sh
```

This script refuses existing run4, uses only run1/source as a read-only baseline,
clones without hardlinks, initializes the fresh target to65532:1001 and affected
0644 modes, and ends with the fixed-default posture check. No agent executes
its Git/chown operations. Partial failure remains evidence; do not delete roots,
repair live state or blindly rerun it. No image rebuild is necessary.

After fresh operator preparation, separate host commands with cwd
`/home/sl/src/baton/v12/python` validate and render concrete inputs:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145261/deployment.py validate
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145261/deployment.py render
```

Use the host boundary with real IDs; managed projected IDs cannot establish
host posture. Retain host outputs, then tuner binds actual final files for the
existing material-delta review. These future inputs do not exist yet; correction
review must not fabricate final configuration acceptance or copy run3 markers.

Only after genuine final review, suitable real host access and explicit owner
authorization of another model attempt can these later held commands run from
the same cwd, provision first and then one ordinary submit/serve:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145261/deployment.py provision
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-145261/run.py
```

Required access stays real host IDs/supplementary1001, scoped run4 writes and
ordinary engine access. No grants for these new paths are asserted or installed
by this preparation. Future review must bind all three execution helpers and
exact rendered inputs. No attempt is authorized now by owner145258. Preserve
actual original reviews, A integration, B independent derived judgments and
coordinator import, both landed changes and terminal Jobs as the outstanding
proof. Report absent B model integration runtime honestly. This correction
removes the observed telemetry interruption without counting unfinished stages
as delivered or adding a planning/hardening prerequisite.

## Costs and deferrals

All three failed runtime runs total560.1007706070232s and stay spent. Prior listed
preparation/diagnosis2.1643190810253747s plus offline test command0.043959831s,
static/continuity0.15002837000065483s and manifest generation0.00123895300203003s
is2.3595462350280596s. Test internal duration is not added twice. Untimed CLI/source reads,
edits/package work, operator duration and billing uncertainty remain additional;
all prior failed validation and review costs stay retained. No reserve transfer.

Keep1200/240/180/120s including B judges within integration120,2CPU/2GiB/512PIDs,
20CPU/20GiB host capacity plus22GiB available memory,16GiB free-storage preflight
and retained-storage stop, existing scratch mounts and declared512MiB capacity
(not a quota). No stats retries, new model attempt, live repair, deadline increase
or broader monitoring work. W144813/W144335/authentication UX/observation/fault-C
and stronger hardening remain deferred.
