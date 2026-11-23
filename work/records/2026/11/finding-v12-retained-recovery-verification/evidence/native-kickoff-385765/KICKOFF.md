# W385625 Stage1-C operator packet — E385765 / M385763

Ready as an operator packet, conditional on the explicit role/provider and execution selection below. No preparation blocker requires a product change, rebuild or new qualification. This turn performs no build/test/instance creation or update/model/live launch.

Source14276917cf4eceaf494dc04fe158aaad2440e7d6; qualified bundle at v12/python/build/out/distro, identity and entire runtime manifest pinned in packet. Preserve build stamp dirty=true/changed_entries11; dossier changes do not require rebuild or repin. Existing image sha256:19eb459b44478f60ee16a61fcc32c2c99dd0132d7d93675adf9fb7afbe5a92b4, tag baton-v12-worker:ac17a5ad; accepted W385694 qualification M385756 reused, not rerun. Template baton.v12.job-template.implementation-review/4; descriptor native-handoff.proposal100m/1 canonical sha256:cf29ab07e507089520ba0c165b0661df0054f17fe35b986b4cf63c9ac713792e. Exact descriptor/profile data in role-contract.json/development-profile.json.

Native development profile native-handoff-heavy/1:7200 provider,9000 stage,21600 queue-inclusive Job,900 verification,0 correction rounds and existing one clarification continuation. Product recovery retains approved9960/4800/3600/900 bounds and exact profile digests from STAGE-1-CONTRACT. TASK.txt3954 characters and self-contained; ACCEPTANCE.md preserves M385735 matrix and adds supported prior Authority ending -> fresh claim, per D4. Source inputs name pinned base versions; later dossier-only planning is carried in task/acceptance rather than silently replacing pinned worker source.

## Concrete owner selection

Existing composer binds Claude CLI2.1.247, model opus, for both roles; it does not offer an alternative provider/model selector. Proposed separate contexts: baton.claude-native on impl-a and baton.reviewer-native on review-a. baton.slaw is the decision recipient; the answering reviewer gets the existing scoped handoff grant through supported bootstrap. No prior same-provider exception or launch grant is transferred. Owner must explicitly select these separate Claude/Opus roles and this native implementation/review execution before any mutating script step. Otherwise this exact packet stops; a different supported provider binding requires a newly reviewed selection, not an invented flag. This is the only unresolved owner choice.

## Commands

Durable operator.sh is copied byte-for-byte to /tmp/baton-w385625-kickoff.sh. Restore it with `cp work/records/2026/11/finding-v12-retained-recovery-verification/evidence/native-kickoff-385765/operator.sh /tmp/baton-w385625-kickoff.sh` if /tmp is cleared. Run each block separately and stop on failure. No main Git operation: prepare materializes its own independent disposable source clone at pinned base, then uses existing bootstrap and composer. Failed prepare leaves its evidence/state for inspection; do not delete/restart blindly.

```bash
bash /tmp/baton-w385625-kickoff.sh check
```

The check is read-only: exact input hashes, source commit inputs, all qualified runtime files/links and bundle identity, image identity, task bound and literal verifier shell syntax. It is not authentication/engine capacity/readiness proof. Once the owner explicitly selects the proposed pair and execution:

```bash
export W385625_OWNER_SELECTION=claude-opus-separate-roles
bash /tmp/baton-w385625-kickoff.sh prepare
```

Prepare creates ONLY new /home/sl/baton-instances/native-w385625-verification-1 and scratch source/run roots; it refuses if any already exists. It composes BOTH /4 workers for this new instance through the packaged CLI, asserts exact descriptors/distinct principals, repeats supported bootstrap with those generated documents, and prints repository/status. No old-instance paths/documents are copied. Existing credential registry slot is referenced, never copied/read into evidence. Require zero Jobs/not serving before create.

```bash
bash /tmp/baton-w385625-kickoff.sh create
```

Create selects /4, explicit heavy profile/provider ceiling, exact task/verification argv, record/scope and source. It retains JSON/report in work/scratch/w385625-kickoff-1, validates /4, full heavy resolved bounds and both admitted lanes. Review output/status before start; failed creation may have reserved identity and must be inspected, not papered over with a new Job.

```bash
bash /tmp/baton-w385625-kickoff.sh start
```

Start repeats read-only pins and admission checks, then existing start/monitor. Monitor exit does not stop execution. If owner selects stop: `just --justfile /home/sl/baton-instances/native-w385625-verification-1/justfile stop`; stop return alone does not prove runtime cessation. Retain run commands/readback, exact candidate/evidence, native independent review and unresolved state in owning dossier. No automatic import/main Git action is selected.

## Validation and limits

operator.sh Bash syntax and embedded Python compilation passed; task length3954, input JSONs/argv and descriptor/profile pinned; read-only check exit0. Full runtime hash inventory matches the existing qualified bundle; existing image identity matches. No repeated tests/build/qualification. Future task acceptance tests do not exist yet: verification must pass after implementation, not during preparation. Running-instance state/resources/credentials are checked by execution tools when selected, not guaranteed here. Independent review of this packet and owner selection remain necessary before live execution.
