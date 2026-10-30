# Proposed input-only useful Job

Task: `template-job-guide-42bed8bb`.
Template: `baton.v12.job-template.implementation-review/1`.
Source selection: `installed` (installation must bind the selected42bed8bb source
or explicitly reviewed compatible artifact; existing instance4 does not qualify).

Statement: Write a reusable operator guide for ordinary v12 template Job creation
and observation using the supported installed command. Explain the supplied task,
source, scope and acceptance inputs, template version and limits, independent
review and held results, failure/recovery boundary and human disposition. Verify
all documented command examples against current supported parsers and behavior.
Preserve the historical instance4 QUICKSTART facts; do not claim source features
are installed there. Deliver documentation, not product redesign.

Initial proposed scope: `v12/TEMPLATE-JOBS.md`; read-only evidence includes
v12/STACK.md, v12/QUICKSTART.md, v12/DESIGN.md, tools/job_manager.py,
tools/stack_command.py, tools/stack.py and python/WORKER-VISIBILITY.md.

Acceptance criteria for create argv and independent review:
- Examples use supported manager create with input-only operands and the exact
  template version; they do not author admission manifests or replace owner APIs.
- Source/installed distinction, actual deployment identities, proposed versus
  executed operations and default/overridden limits remain explicit and truthful.
- Monitoring is read-only; query time is not worker contact; unknown activity is
  not success; ending the monitor does not stop scheduling.
- Implementation completion, independent verdict, held proposal, human acceptance
  and Git integration are distinguished. Failure/retry and runtime-cessation
  prerequisites are stated without silently retrying or claiming stop is cleanup.
- Semantic evidence checks command order/options and statements against owning
  implementations, not only headings/byte count. Review binds the actual candidate.

Proposed limits: provider3600s / verification900s per invocation, two-stage
implementation/review, report-and-hold, no integration stage. Finite additional
correction-turn selection must be explicit before any serving. Preparation is
not execution approval. Do not force a correction solely to spend a live run;
retain natural outcome and limitations.

The preparer supplies actual fully ordered commands and deployment operands in
its reviewed output. This input document is review/selection evidence, not a
file that manager create consumes and not a custom runtime task manifest.
