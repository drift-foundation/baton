# Plan

Decision and implementation handoff paths:

- `work/records/2026/09/finding-v12-production-runtime-conversation/FINDING.md`
- `work/records/2026/09/finding-v12-production-runtime-conversation/PLAN.md`
- `work/records/2026/09/finding-v12-production-runtime-conversation/PROGRESS.md`
- `work/records/2026/09/finding-v12-production-runtime-conversation/evidence/repro-cross-session-replay.py`

1. [done, reviewer revalidation 2026-09-04] Reproduce the idle W71917 runtime
   and confirm that production starts the container without delivering Work.
   The pipe-replay research remains useful historical evidence but is not the
   production design.
2. [done, approved and reviewer-revalidated 2026-09-04] Define one
   attempt-private exchange delivery outside `inputs` and `workspace`, with a
   manager-owned read-only command namespace and worker-written untrusted event
   namespace at fixed container targets. One closed `describe`/`work` sequence,
   its pre-dispatch receipt, state events and terminal outcome are canonical,
   digest-correlated, atomically published files. Raw provider streams and new
   `result/logs`/`result/output` trees are explicitly outside this Work.
3. [done, W81857 implementation 2026-09-04] Version the launch document to select
   `baton.worker-exchange/1`, extend the typed launch/exchange delivery and OCI
   fixed mounts, and make `baton_worker.main` run the durable directory scanner
   in production while retaining launch `/1` stdin framing only for explicit
   diagnostics/tests. Reuse the one existing operation handler and atomic
   completion publisher.
4. [done, W81857 implementation 2026-09-04] Publish the worker receipt before provider
   dispatch, reconstruct spent work from durable files, and publish only closed
   credential-safe state/terminal documents. Exact replay, rescan, manager
   restart, and worker re-entry after receipt must never start a second
   provider turn.
5. [done, W81857 implementation 2026-09-04] Add the production Job-manager
   post-launch pass
   and exchange observation as optional deployment capabilities. Publish once,
   rescan level-triggeredly, keep watchers advisory, add no Job-store receipt,
   and version status so a started container is not reported as active work.
6. [done, W81857 implementation 2026-09-04] On one valid answered terminal, independently
   validate the existing `/output/output.json` and continue through the
   already-ruled successful quiescence, disposition, freeze, intake, and ending
   owners. Report fault/loss/incomplete truthfully; do not add general
   abandonment/retry, pool, checkpoint/review, integration, or log policy.
7. [done, W81857 implementation 2026-09-04 — source regressions and the
   real-container gate, the latter recorded in
   `evidence/gate-real-container-2026-09-04.json`] Add the exact static, atomic-publication,
   manager-race, restart-window, correlation/digest, malformed/untrusted-file,
   secret-surface, status, output, and failure-containment regressions listed
   in FINDING.md. Prove a fresh immutable real worker image continues through
   a Job Manager restart and produces one provider invocation and one durable
   terminal/output result without production stdin/stdout.
8. [awaiting independent review] Bind the proposal digest and changed path set;
   verify the file ownership boundary, atomic publication, restart recovery,
   exact one provider invocation, credential-safe durable evidence, and
   successful output/ending composition before integration.

`worker_entry.converse` may remain a diagnostic/test transport. It is not the
production control or completion path and the W71917 manual stopgap does not
satisfy this plan.

## Still owed before this record can close

- Independent review of the digest-bound proposal (item 8).
- The authorized operator's restoration of the proposed target path set to the
  declared base or absence, so `baton.merge`'s whole-path preflight can run.
  That is an integration act and is not the implementer's.

The real-container gate of item 7 is DONE and its evidence is
`evidence/gate-real-container-2026-09-04.json`, produced by
`evidence/gate-real-container.py` against a freshly built immutable image
`sha256:db9f397171153338ce068b46a7c9ab48c79b80d9f1ad1db4c149541a5eb8199b`. It
proves the transport, the restart boundary, exactly-once dispatch and the
durable result. It does NOT prove that a commercial provider was reached: the
reference image's provider is `ScriptedAgent`. The dogfood image injects a real
provider at the same documented seam and needs a credential this gate
deliberately does not require, so running it there is a separately authorized
operator act.
