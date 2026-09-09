# Implement the integration observation boundary

W126558. Owner126545 grants this exact provider scope. Handler baton.claude via
baton.impl; independent review baton.bug. Claim before execution. Read FINDING,
OBSERVATION and the parent allocation before editing; revalidate against source.

Current state: independently accepted in `review-2026-09-09T09-20-55Z.md`,
review claim126698. All three prior findings are resolved; OBSERVATION.md
revision1 is unchanged. Exact accepted bytes/modes are retained under
`evidence/accepted-126698/`. No provider implementation remains. Release the
gate for W122060's separately approved two-path consumer; real terminal handoff
and ordinary/restart joined acceptance remain there.

## Exact ownership

Only these paths, relative to `v12/python`, plus this dossier's attributable
PROGRESS/evidence:

1. `src/baton_v12/job_manager/delegation.py`
2. `src/baton_v12/job_manager/projection.py`
3. `tools/job_manager.py`
4. `tests/job_manager/test_delegation.py`
5. `tests/job_manager/test_status.py`
6. `tests/job_manager/test_exchange.py`
7. `tests/job_manager/test_tool.py`

The parent owns stage_execution.py and test_stage_execution.py. Do not edit
those, its other reserved paths, the registry, store schema, documents.py,
manager.py, runtime, integration driver or Authority. No additional source
allocation follows from this plan.

## Sequence and acceptance

1. Implement the exact optional reader/document in OBSERVATION.md. Pin any
   necessary within-scope clarification as explicit history before code and
   flag it in the handoff; do not silently change the consumer interface.
2. Bind every supplied integration observation to the canonical claimed offer,
   stage, episode, attempt and fixed assignment. Map its closed states using
   existing stage vocabulary and derive conclude where specified. Preserve all
   ordinary exchange behavior and prior failure precedence.
3. Wire the optional callback into ManagerOperations and the status observation
   wrapper by name. A status reader cannot gain a serving or refresh capability.
4. Add focused tests for absent callback/backward compatibility, unstarted and
   pending, answered/conclude, committed completion/no act, held/uncertain,
   missing completion evidence, foreign attempt/offer/assignment and malformed
   documents. Include the serving sweep selecting conclude rather than dispatch
   and read-only wrapper denying external acts. Bound document fixture/expected-
   member additions to the optional integration member; preserve all existing
   non-integration expected behavior and negative assertions. These scheduled
   test changes are explicitly approved by M126545.
5. Declare the evidence question before running tests; enforce cumulative20s
   across all test/probe processes. Use focused selectors, retaining every run
   and elapsed time; no unchanged provider or full-suite repeats. At the limit,
   stop and hand back the exact remaining question.
6. Record baseline/final hashes and modes for every owned path, exact changes
   to existing tests, commands/results and limitations. Return to baton.bug
   for independent acceptance. W122060 remains gated until acceptance and then
   consumes this interface in its already approved two-path tuner pass.

This is an implementation provider, not a new planning Job. Its independently
acceptable result is the generic reader and scheduling contract; it makes no
claim that the real integration terminal handoff or final lifecycle is proved.
