# Finding: specify the v12 worker-control API and typed manifests

Canonical Baton Work: `W1439` (`43c55d4b-W1439`).

Child of `work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/`.

## Assignment boundary

Produce the normative, transport-independent outer worker-control contract and
typed manifest family. Reuse the signed-off W151 assignment identities,
ownership split, transitions, exact replay/retirement rules and immutable
workflow receipts. Do not implement protocol, authority, manager, runtime,
adapter or application code.

## Required design output

The specification must define:

1. protocol family and semantic version negotiation, mandatory core
   capabilities, namespaced optional extensions, strict major-version refusal,
   and explicit unknown-field behavior;
2. request/response/event/error envelopes with correlation, operation identity,
   full `work_ref`/`assignment_ref`, manager-observed ordering/time, payload
   digest, size limits, redaction and retry semantics;
3. runtime-neutral operations for offer/accept/decline, start, cancel, inspect,
   activity, freeze, collect, publish, retain and destroy without exposing
   Docker, Podman, SSH or vendor process vocabulary;
4. typed input-source and output descriptors for at least `git`, `directory`,
   Git change proposal, directory result and record output, with canonical
   destinations, immutable identity, constraints and credential-free URIs;
5. assignment, runtime-attempt, frozen-result, proposal, verification,
   technical-review, approval and integration receipt manifests, including
   the exact digests each binds;
6. one closed portable error taxonomy separating refused, ambiguous,
   unavailable, policy, integrity, stale-generation and runtime-observation
   failures; and
7. canonical examples and invalid vectors sufficient for schema and
   effectively-once model tests.

## Acceptance boundary

- Every durable identity is full and structured; compact selectors are display
  only.
- Bearer tokens and credentials never enter persisted manifests, events or
  artifact locators.
- A control message cannot grant authority beyond the current live assignment,
  and no runtime report can manufacture Baton state.
- Runtime diagnostics may be extended but cannot alter portable lifecycle
  semantics.
- The design explicitly supersedes only `0-spike` envelope choices and leaves
  the accepted PoC evidence valid in its bounded scope.

## 2026-08-21 design record

- **Confirmed:** W151 remains the normative owner of authority state,
  assignment generation, exact claim settlement/retirement, cancellation
  fencing, runtime-quiescence gates and workflow-receipt authority. This child
  imports those rules and does not redefine them.
- **Confirmed:** `SPEC.md` defines the proposed `baton.worker-control` and
  `baton.worker-manifest` `1.0-design` vocabulary. Core objects are sealed,
  exact minor versions are negotiated, portable capabilities are closed, and
  extensions must be explicitly negotiated.
- **Confirmed:** `schema/worker-control-1.0.schema.json` defines strict bodies
  for all 17 portable control kinds plus input, assignment, runtime-attempt,
  frozen-result, proposal, verification, assessment, technical-review,
  approval and integration documents.
- **Confirmed:** `evidence/vectors.json`, `evidence/contract_model.py` and
  `evidence/test_contract_model.py` are provider-free design evidence. They do
  not import Baton product code or alter `v12/` runtime behavior.
- **Proposed for approval:** freeze the five decisions listed in `SPEC.md`
  section 14 as the outer contract consumed by dependent ACP-boundary Work
  W1440 and conformance Work W1441.
