# Plan — fresh-runner Baton connection handoff

1. **Accept the cross-team transfer** — **done 2026-08-11**. Record the
   workflows reproduction and preserve the existing no-inference rule.
2. **Inventory real runner launch surfaces** — observe how each supported agent
   host starts fresh/resumed sessions, which structured metadata it can inject,
   and where current deployments choose executable/config paths. Do not infer
   undocumented behavior from one runner.
3. **Rule ownership and scheduling** — choose the carrier owner and decide
   whether an operational correction precedes 1.1 release, joins the RC soak,
   or is a next-major stable-deployment gate. Keep it separate from polling
   reliability and from implicit CLI discovery.
4. **Rule the connection descriptor** — pin required fields, scope, provenance,
   read-only validation, failure taxonomy, restart lifetime, and the atomic
   live-first cutover update.
5. **Define deployment integration** — decide whether `just deploy` emits an
   executable fragment, how a supervisor combines it with an external config,
   and how production/candidate/retired choices remain explicit.
6. **Implement the smallest owned adapter** — only after the prior rulings;
   never scan repositories, mailbox directories, process lists, shell history,
   or retired installations to guess a pair.
7. **Verify across fresh sessions** — use the acceptance cases in `FINDING.md`,
   including missing halves, mismatches, unhealthy authorities, candidate
   opt-in, restart/compaction, atomic cutover, and several retired decoys.
8. **Document and independently review** — update onboarding/deployment/runner
   guidance without hard-coding local paths, then obtain cross-team confirmation
   that the workflows reproduction no longer requires inference.

`baton.implementer` creates and exclusively writes `PROGRESS.md` when this
finding becomes the current serial implementation item.
