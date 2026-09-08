# Ordinary-test evidence at integration admission

Work W112029, canonical binding baton:work/records/2026/09/finding-v12-ordinary-test-admission/.
Created by baton.codex under W110772 claim112022, owner112006, 2026-09-07.
Ledger parent W103068; separate top-level dossier avoids exceeding child depth.

## Accepted decision and discovery

**Confirmed:** W110772 independent review111949 found that lifecycle correction
and ordinary-test admission are independently deliverable. Owner112006 accepts
that split and assigns this slice to baton.impl, while tuner retains W110772
lifecycle paths. This record owns the ordinary-test implementation assignment;
it does not duplicate W110772's dossier binding.

**Confirmed baseline:** integration.driver.admit_accepted has no required_tests
operand and its receipt path unconditionally publishes passed. The worker
already executes the task's actual verification argv through _verify, records
its answer in result.json/verification.txt, revalidates candidate bytes and
publishes the private-line commit. Frozen proposal metadata does not yet expose
that supervisor-owned ordinary-test observation to admission. An accepted
technical review therefore cannot justify the current unconditional receipt.

**Accepted, M111752/owner111888/owner112006:** this milestone uses ordinary
implementer tests plus independent review. No separate clean verifier actor,
service, image, Job stage or configuration schema is required or authorized.
The Authority raw passed receipt may represent actual ordinary required tests,
with explicit provenance; it must not claim a clean verification run. Technical
review alone cannot substitute for failed/unrun required tests. Existing red
gate exemptions require an exact owner ruling; this assignment grants none.

Decision source and detailed acceptance contract:
baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-review-verdict-channel/FIRST-PROOF-PLAN.md.
Its serial-all-path allocation is superseded by owner112006 and this split;
its ordinary-test semantics and numbered path identities remain accepted.

## Accepted implementation contract

1. In v12/worker/claude_agent.py expose the existing actual _verify observation
   on the proposal output's result_metadata under baton.git-ordinary-tests/1.
   Closed fields: task_id, task_digest, argv, status, base, head. task_digest
   hashes the exact bounded task bytes consumed. Derive values from the owned
   task and actual subprocess answer, after candidate revalidation/publication;
   never trust a model-written passed flag. Preserve result.json behavior,
   verification.txt and the existing closed four-field proposal namespace and
   review namespace. No additional execution, output directory or capture layer.
   Failed status remains failed; absent/unrun stays absent or explicitly null
   under the documented closed reader contract.
2. integration/driver.py owns the format-specific evidence reader. Resolve the
   checkpoint's exact producer and retained proposal, frozen result and manifest;
   compare assignment/generation, result/manifest/artifact, input/policy identity,
   proposal base/head and checkpoint head through existing owners. Retained
   evidence must remain resolvable after normal output cleanup.
3. Add required_tests to admit_accepted as a trusted closed selection containing
   task_id, task_digest, exact argv and input_manifest_digest. W103083 will derive
   it from its already-held implementation task bytes for this Job/producer,
   including correction attempts. It supplies requirements, never an observation
   or passed flag. This Work does not edit assembly files or choose another
   producer's configuration.
4. Only an actual status0 observation for those exact requirements and accepted
   checkpoint may produce passed. Validate before any receipt/admission side
   effect. Bind frozen result/observation and requirement digests and an explicit
   ordinary-tests workflow marker into deterministic receipt/operation identity.
   Use an ordinary-tests identity prefix. Existing different receipts conflict;
   never overwrite or replay historical fabricated passed as valid evidence.
   Preserve Authority/session capability checks, current-target checks and
   review/approval separation. Do not change any reviewer attempt axis.

## Exclusive file and progress ownership

baton.impl, resolved to baton.claude, owns FIRST-PROOF-PLAN paths 3/4/7/8 and
conditional 10, exactly:

- v12/python/src/baton_v12/integration/driver.py.
- v12/worker/claude_agent.py.
- v12/python/tests/integration/test_driver.py.
- v12/python/tests/manager/test_claude_agent.py.
- v12/python/tests/manager/test_dependencies.py: only the exact new required_tests
  operand declaration if required, preserving inventory assertions.

Owner111888 explicitly scheduled bounded test expectation transfers: failed or
unrun required-test refusal belongs at actual admission, with zero verify,
review, approve and admit calls before refusal. Add actual trivial-command
execution through existing _verify and public frozen-result/custody/Authority
consumers with deterministic external transport. No mocked passing observation.
Cover positive, nonzero, unrun, wrong task/argv/digest/head/generation, conflicting
receipt and retry. Preserve unrelated worker/review/provider assertions. Enumerate
every actual assertion change and return digest-bound candidate bytes to review.

The claimed implementer is the sole current PROGRESS writer here and appends
attributable implementation episodes. Reviewer owns planning/review entries.
W110772 tuner owns review_cycles, review_driver, their two test modules and
REVIEW-CYCLES.md; this Work edits none of them. integration_checkpoint's public
answer schema is the stable seam, not a new interface negotiation.

## Dependencies and limits

The two implementation slices may run independently with disjoint files.
Their joined independent acceptance must precede W103083/W110935/W106673.
Neither individual sign-off releases that aggregate gate. W110935 also waits
for the shared claude_agent bytes through this gate; do not overlap its worker
edits. W103083 retains serving and task selection derivation; W110934 retains
the OCI boundary and its current disposition. Authority, intake, attempts,
schemas, OCI, worker recipes and general verifier code are outside this scope.
Record any concrete missing interface before widening; no speculative framework.

Revalidate these claims at implementation start. Run focused changed suites
and appropriate source/inventory checks once, retain exact failures, and reuse
unchanged broader evidence. No live runtime, provider or target execution is
authorized. The first producer evidence and lifecycle joined check uses public
owners and deterministic external transport, not production deployment.


## 2026-09-07 — coordination finding during claim112022

**Observed agent misuse, not a demonstrated Baton defect:** the reviewer created
W112029 and lightweight joined Work W112039 temporarily on baton.ops to avoid
premature execution. A subsequent block work=W112039 on=W110772 refused because
baton.codex is not a resolved handler of baton.ops. No dependency was added.
The canonical reroute help explicitly identifies reroute as the owning-team
operation for open unclaimed Work; use that authorized routing operation to
move the new Work to baton.bug for graph setup, then route the completed
assignments as owner112006 instructed. Do not mutate the store or impersonate ops.
