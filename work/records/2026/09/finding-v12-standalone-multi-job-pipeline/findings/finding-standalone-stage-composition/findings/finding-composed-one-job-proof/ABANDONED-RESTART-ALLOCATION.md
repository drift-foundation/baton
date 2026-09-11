# Current disposition — approved by owner128669

Current clarification2026-09-09: all three providers are independently accepted
at the exact reviews listed in FINDING.md's17:27Z entry. Standing W71830 test
authority supersedes older additive-only/per-method permission limits below;
record test paths/reasons without per-test gates. B's cap was extended to25s
by owner129177; A/C caps remain20s. W119114's600s carry is unchanged. Earlier
allocation text below remains decision history; PLAN.md is the current sequence.

Owner128669 in T119114 explicitly approves the exact eleven-path A/B/C split
and named gap-test conversion below. The earlier proposed/pending language is
superseded; preserved below as decision history. Implementation is serial through
baton.impl returning baton.bug, with independent acceptance before consumption.

| Provider Work | Permanent record and pinned public contract |
| --- | --- |
| A W128682 | baton:work/records/2026/09/finding-v12-abandoned-cleanup-discharge/CONTRACT.md |
| B W128692 | baton:work/records/2026/09/finding-v12-abandoned-checkpoint-restore/CONTRACT.md |
| C W128698 | baton:work/records/2026/09/finding-v12-abandoned-episode-replacement/CONTRACT.md |

Provider tests remain additive,20s cumulative each. W119114 keeps the exact
approved conversion, bounded glue and final manifest/custody proof, with its
existing600s usage reconciled and carried. No broader retry feature or source
scope is authorized. Predecessor acceptance remains a gate, not assumed from
this allocation approval. Pinned under W119114 claim128673 before dispatch.

---

# Proposed bounded abandoned-correction restart allocation

Prepared by baton.codex, claim128617, 2026-09-09. **Proposed; owner scope decision
required before implementation.** The already-confirmed restart acceptance is
not being reopened. This supplies the missing provider allocation, not a new
planning Job, deadline policy or generalized scheduler retry feature.

## One trigger and outcome

An explicit operator/Route-policy declaration abandons a started, unfinished
correction with no published result of its own. The existing abandonment owner
fences the exact assignment and positively removes the runtime. Recover only
from the last committed changes-requested handoff and its retained checkpoint;
retain prior publication/route/verdict/custody and discard only uncommitted
private scratch. A fresh assignment may write only after owned exclusion and
checkpoint restoration. Unknown external effects remain held. A timeout is not
an abandonment declaration.

## Proposed independent deliveries

Paths below are relative to v12/python. Each provider gets its own bound Work,
claim, permanent top-level dossier and independent acceptance before a consumer
uses it. These are implementation deliveries, not extra planning Jobs.

| Delivery / proposed Handler | Exact proposed path set | Public boundary |
| --- | --- | --- |
| A: committed abandonment evidence and gate discharge / baton.impl | src/baton_v12/worker_manager/intake.py; src/baton_v12/worker_manager/__init__.py; tests/manager/test_intake.py | Read and cross-bind the actual abandonment intent, fixed assignment, runtime and committed destroy result; discharge only that generation's gate on positive absence. Preserve ordinary discharge's existing cleanup-family contract; add a separate abandoned-family boundary. |
| B: restore the abandoned correction's checkpoint / baton.impl, after A | src/baton_v12/worker_manager/review_cycles.py; src/baton_v12/checkpoint_profiles.py; tests/manager/test_review_cycles.py; tests/manager/test_checkpoint_profiles.py | Consume A's public committed evidence, identify this attempt's active writer and its based checkpoint, exclude the old worker before any restore write, restore only its private mutable checkout and revoke its writer, retaining checkpoint/custody identity. Publish/read a durable restart-preparation outcome; never merely relabel writing as correction-ready. |
| C: authorize exactly one replacement episode / baton.impl, after A/B | src/baton_v12/job_manager/documents.py; src/baton_v12/job_manager/episodes.py; tests/job_manager/test_documents.py; tests/job_manager/test_recovery.py | Cross-bind A/B evidence to the actual Job/stage/episode/attempt and committed handoff, record an explicit recoverable abandonment ending, and let existing replacement logic create one successor. Preserve the unrelated issued-offer abandoned-after-restart semantics. |

Keep all three serial initially; revalidate public signatures and current bytes
at each handoff. Public operations may be named by the implementing owner, but
selection must be by owned attempt/episode identity rather than caller-supplied
claims of absence or fabricated receipts. Repeated calls and lost answers must
recover journalled results, never repeat committed publication/integration or
create a second live writer/episode. No Authority policy/configuration/schema
expansion is proposed. If a listed boundary cannot be implemented in its path
set, report that exact gap before edits outside it.

Tests are additive within each provider set. Preserve all existing assertions,
including ordinary-family refusal behavior. Each provider declares focused
questions and enforces a20s cumulative process budget, retaining exact commands,
outputs, elapsed times and failed iterations. Reuse existing fixtures and
accepted provider evidence. No broad source inventory or full suite per provider.

## W119114 consumer and proof

After A/B/C independent acceptance, W119114 keeps its existing five-path scope
with serving glue/tests restricted to tools/stage_execution.py and
 tests/tools/test_stage_execution.py unless another already-owned path is needed
and explicitly accounted for. Wire public recovery through the explicit
abandonment path; ordinary ticks then perform the fresh assignment. No raw store
edits, hidden reset, synthetic verdict, or engine-state guess.

The proposed scope decision explicitly schedules converting only
UnfinishedWorkIsFencedBeforeAnythingRepeatsIt.
test_no_fresh_assignment_follows_the_declaration_and_why from the current gap
assertions into the positive replacement proof. Retain its fixture and all
other assertions; add negative running/uncertain/foreign-evidence cases. Prove
no new writer before exclusion, restored checkpoint bytes after scratch loss,
exactly one fresh assignment and unchanged committed effects across replay.
Reuse the terminal lifecycle for corrected-result manifest/artifact/pin checks.

Keep W119114 open for final joined acceptance and W103083 downstream. Reconcile
its current reported353.487s approximate carry-in against the600s declared
budget before more consumer runs. Existing W115981/W48697 own the separate
unresolved whole-suite checks; no blanket scanner or assertion exception follows.
