# W71879 run3 validation host boundary — tuner145012

Concrete final rendering is incomplete. Owner144993 reports the reviewed fresh
operator preparation, including its fixed-default target check, succeeded.
The managed read-only preflight instead sees target uid/gid65534, refusing
`gid 65534, expected workspace gid 1001`. Its exact standalone target_posture.py
command confirms the same result before any write. Both /proc/self/uid_map and
gid_map contain only `1000 0 1`; foreign target ownership is not represented by
this namespace. Target/.git directories show2775 and the affected greeting file
shows0644. These observations do **not** establish incorrect host ownership or
contradict the operator's successful host check. No target repair is proposed.

The current managed boundary cannot validate the required host65532:1001 identity.
Exact validate/render commands have no matching rule in the two installed rule
files, as retained in evidence/run3-freeze-145012/command-boundary.json. They were
not executed after the earlier read-only gate refusal. No final frozen-config,
validation.json, image-selection marker or execution-review marker exists. The
run3 root contains only source, target and integration-workspace. No production
Authority/control state, runtime, submission or credential delivery was created.

## Preserved review and evidence

All25 candidate files still match review-2026-09-11T14-18-17Z.md by hash/size/mode:
prepared-144859/candidate-manifest.json SHA256
6b4121c4f36c3b881e4fd2d8edcc09ac358c6c28b5b98b787c1a7f1185aa9b33.
All159 prior run2 package files and four source-requirement bindings also match.
No helper, task, policy, image, product source or test was changed. Neither failed
run was repaired. Independent correction review remains accepted; final actual
configuration review remains outstanding. This is a deployment observation,
not a newly established Baton product defect or reason to reopen that correction.

Evidence: boundary-observation.json, command-boundary.json and spending.json
under evidence/run3-freeze-145012/. The initial failed preflight command cost
0.032879572s and retained continuity/namespace check0.003486240006168373s.
Listed preparation/diagnosis is now1.663012100016991s, separate from failed runtime wall
524.7600469310128s. Other tool calls with microsecond-only timing do not supply
comprehensive measurements; untimed reads/rule checks/edits/operator preparation
and billing uncertainty remain additional. No model budget or provider reserve
was spent or transferred in this claim.

## Exact continuation

Return incomplete Work through baton.bug, Next baton.ops. The operator can run
the following two reviewed preparation commands on the host, or supply their
exact managed host execution boundary so tuner can run them. Keep the real host
IDs visible; do not weaken the posture helper, reinterpret65534 as a passing ID,
change target ownership, rerun operator-prepare.sh or reconstruct state manually.
This is the missing execution boundary for the existing preparation, not a new
planning, Git, image-build or model-run prerequisite.

Required cwd for each separate command: /home/sl/src/baton/v12/python.
First validate (temporary public Authority under /tmp; no production submission):

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/deployment.py validate
```

Then render (writes the previously absent final configuration in the dossier):

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/deployment.py render
```

Both commands recheck target posture and actual source/target baseline before
writes. The reviewed deployment.py SHA256 is
9075d36e5786d4f3434a758d3ac7f754dbc8c3bccfcba6eff44c8f6385f49ec9;
target_posture.py SHA256 is
62edccc553861eed2ed8f05d44ac47b6b38e8e6b86de2dd4994608028d6cfd97.
Return this Work to tuner after successful outputs or exact access is supplied.
Tuner then binds concrete final inputs and sends the existing material-delta
review. Host observations must be retained as host evidence; a managed projected
stat must not be represented as successful host validation. Partial failure stays
retained; no automatic repair or repeated preparation.

For clarity, the later provision/run commands remain **unauthorized now**:

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/deployment.py provision
```

```text
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/prepared-144859/run.py
```

They require final independent acceptance, genuine review/image markers, suitable
host access and the owner's explicit authorization of another model run. Owner
144993 expressly preserves that hold. Final material review and actual independent
original/derived judgments, both landed changes and both terminal Jobs remain
outstanding. Do not infer success or run authority from preparation acceptance.
Preserve1200/240/180/120s (B judges within integration120), all resource/storage
limits and run1/run2 spending/evidence. W144813/W144335/authentication UX,
observation/fault-C and stronger hardening remain deferred.
