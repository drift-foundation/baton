# V12 API model adapters and testing roles

Recorded 2026-09-07 by baton.prompt at Slawomir's request.
Canonical Work: W111793, bound at creation111793 and routed to baton.ops.
Status: deferred v12 roadmap; operator parking requested. No implementation
or runtime execution is scheduled. The bound Baton Work is the lifecycle owner.

## Confirmed direction

Preserve both provider API adapters and their concrete testing uses for later
v12 work. They are outside W71830's minimum standalone critical path. Resume
only through an explicit later scheduling decision, not automatically when
W71830 closes.

The earlier adapter ruling remains in
`baton:work/records/2026/08/finding-v12-isolated-agent-workers/FINDING.md`,
"API-backed model workers without a required vendor CLI". This record owns
the deferred follow-up, including the testing use cases discussed afterwards.

## Provider adapters

Run provider-specific wrappers inside Docker against remote model APIs, with
no required vendor CLI or coding-oriented native agent. Preserve one stable
Baton worker contract. Keep reusable assignment, conversation, tool execution
and artifact handling separate from provider authentication, requests,
responses and streaming. A supported model should be replaceable through its
adapter/runtime profile without changing Baton's workflow protocol.

Track the service provider and actual underlying model separately. Discover
or declare capabilities such as tool calling and search rather than assuming
every compatible API supports them. General research and analysis are useful
initial workloads as well as coding and testing.

Venice and Duck.ai were examples, not selected providers or certified models.
Supported programmatic access, model capabilities and useful task performance
need checking when this work is resumed. Venice documents a chat API and tool
calling at https://docs.venice.ai/api-reference/endpoint/chat/completions.
No credentials, provider subscription, API execution or browser automation
is authorized by preserving this roadmap.

## Test-engineering uses

A future visible agent/role may develop and execute regression, performance,
stress, fuzzing and vulnerability tests. It should return reproducible cases,
commands, actual outcomes and retained evidence through ordinary tracked Work.
Tests and findings remain independently reviewable; the model's assertion of
success is not an execution result.

Security testing against designated project targets is a specific motivation
for trying alternative models. Slawomir wants models that can handle the
necessary adversarial testing tasks without inappropriate refusals. Provider
selection remains open: refusal behavior alone does not establish technical
capability. Evaluate reproducible findings, tool use and execution reliability
on bounded project test cases. The worker's assigned target/resource boundary
remains controlled independently of the selected model.

A model-operated verification stage was also discussed: receive an exact
candidate and implementation results, run configured tests, then advance to
code review or return failures for correction with visible status and evidence.
This is a future option, not a current pipeline requirement or a decision to
create a separate verifier service.

## Current milestone boundary

For W71830, the implementer runs ordinary required tests and the independent
reviewer may run additional or broader tests. Neither these adapters nor a new
testing/verification role is a prerequisite. The current ruling is in
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md`,
"Current verification is implementer testing plus review".

## Questions for a later bounded assignment

- Which first provider/model and supported API best prove the adapter boundary?
- Which existing task runner and worker image facilities can be reused?
- Which one research or testing task gives a small, reproducible first proof?
- Is testing assigned to an existing worker role or a separately named role?
- What target/resource scope and evidence make each test campaign reviewable?

These questions are deferred, not additional research gates for W71830.
