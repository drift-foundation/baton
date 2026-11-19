## Current — registry correction complete, awaiting delta review

Supersedes prior active/current status entries below. E385282 correction is complete; current candidate candidate-option-a-registry/manifest.json and HANDOFF-OPTION-A.md. Full registry/groups and focused runner/accounted checks pass. No broader implementation selected. Post report, pass baton.decide and verify release.

## Current — Option A candidate ready for independent review

Implementation and focused verification complete under E385275. HANDOFF-OPTION-A.md and candidate-option-a/manifest.json are current. Prior in-progress/research sections below are historical; Options B/C remain unapproved. Post report, pass to baton.decide and verify release.

## Current — Option A approved for implementation

Supersedes research-only Current sections below for Option A only. See FINDING owner approval and CLI-OBSERVABILITY-ADDENDUM.md Option A. Retain schemas/CLI; shared interpretation and15-second freshness using existing observations. Options B/C, new telemetry and full envelope remain unapproved. Claim before implementation.

## Current — research refresh only, implementation unapproved

CLI-OBSERVABILITY-ADDENDUM.md completes M385268 research refresh. Preserve original DESIGN-PROPOSAL.md as history. Current next action: independent review and explicit owner decision on the addendum; implementation remains unapproved.

## Current constraint — CLI-only execution

Owner explicitly requires retaining CLI invocation. Research existing logs/transcripts/output and compatible CLI streaming modes; unavailable interactive queries are acceptable. Do not propose SDK/App Server migration. All implementation and CLI behavior changes remain subject to owner approval after research/design. See FINDING latest clarification.

# Research/design plan

1. Claim; inventory existing collectors, event paths, publisher/read model and consumers. Cite exact code and owning records; distinguish available signals from gaps.
2. Propose one versioned shared observation model and reusable query/interpretation boundary. Specify identity, sampling/observation times, freshness, unknowns, bounds, restart/retired-attempt handling and per-Job attribution.
3. Compare minimum useful phase with later metrics; assess CPU/memory/file-count cost and security without building new collectors. Explain status/monitor/TUI reuse and no duplicated logic.
4. Deliver DESIGN-PROPOSAL.md with alternatives/recommendation, schema examples, component ownership, implementation slices, focused deterministic acceptance and explicit unresolved owner decisions. No product edits, normative design changes or live operations.
5. Post report in owning thread; pass to baton.decide and verify claim release. WAIT for explicit owner approval before coding.

Ownership: codexpc writes this research dossier; K current pilot correction/operations and existing implementation paths are untouched. This is not authorization to start a TUI or a broad telemetry framework.

## 2026-11-19 — research completion

Steps 1–4 complete: DESIGN-PROPOSAL.md, RESEARCH-EVIDENCE.md, SOURCE-MANIFEST.json. Step 5: post proposal T385263, pass baton.decide and verify null handler; receipts retained under evidence/. Next actionable state after handoff: independent review and explicit owner approval, no coding.

Step 5 complete: M385265, E385266; release verified. No active implementation claim remains.

## E385275 implementation in progress

M385273/OBS-2 revalidated. Ownership posted M385276: new tools/job_observation.py, tools/job_viewer.py, tools/stack.py, new tests/tools/test_job_observation.py, tests/tools/test_job_viewer.py, tests/tools/test_stack.py, JOB-VIEWER.md (all under v12/python), and this dossier. Existing test changes update owner-selected 15-second and known-zero behavior; new cases prove attribution and shared interpretation. Owner DESIGN and K pilot paths untouched. Baseline bytes in evidence/option-a/base.

Option A review handoff complete: M385278, E385279; claim release verified. Next action belongs to independent review.


## Current continuation — Option A registry correction

Codexpc to address review-2026-11-19T18-59-06Z.md, refresh candidate and return for delta review. No broad test run or deployment selected.

E385282 active correction: register test_job_observation with isolation rationale, prove full registry/group completeness read-only and run focused runner/new-module checks only. Preserve earlier candidate and issue a new seven-path candidate for delta review.

Registry correction handoff complete: M385285, E385286, claim release verified. Independent delta review is next.


## Current disposition — source accepted, human checkpoint pending

See review-2026-11-19T21-19-33Z.md. Registry correction resolved; accepted candidate 7c1da2d2…. Owner Git checkpoint next. Installed rollout remains separate.
