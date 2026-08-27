# Plan: first v12 Docker ping-pong proof

1. [blocked on W6633 and W6634] Revalidate the final reference-worker,
   artifact-neutral input/output and credential contracts.
2. [pending] Add the smallest Python orchestration path for one consent claim
   followed by one fresh execution attempt; reuse reviewed manager and adapter
   components rather than creating a parallel lifecycle.
3. [pending] Add a documented `just ping-pong` operator entry point and a
   deterministic ping input/pong output fixture.
4. [pending] Run the real-Docker proof, retain correlated lifecycle and cleanup
   evidence, and verify Docker absence fails visibly.
5. [pending] Return for independent review. On satisfying closure, unblock
   W6636 for its broader restart, race, failure, cancellation and portability
   matrix.

## Replan — 2026-08-26 tracer-bullet first

The five steps above are superseded for this Work because they wait for the
production components whose value the demo is meant to test.

1. [ready after dependency removal] Remove W6633 and W6634 as blockers while
   retaining W17110 as a prerequisite of W6636.
2. [pending] Build the smallest clearly labelled spike-only Docker image with a
   deterministic worker that reads a mounted `input.json` and writes the
   correlated `output.json` last.
3. [pending] Add one Python operator path, preferably `just ping-pong`, that
   stages read-only input, runs the real container with separate writable
   output, validates `pong`, and positively cleans up.
4. [pending] Run the demo and retain concise evidence for image identity,
   mounts, correlation, result, exit and cleanup. Treat Docker absence or a
   malformed/missing result as failure.
5. [pending] Independently review only the bounded spike claim. Record what the
   experiment teaches W6633, W6634 and W6636, then close without representing
   the spike as production conformance.

## Replan — 2026-08-26 real Claude then Codex

The deterministic fake-worker portions above are superseded. Keep the
tracer-bullet implementation intentionally disposable, but exercise real
provider runtimes.

1. [ready after dependency removal] Remove W6633 and W6634 as blockers while
   retaining W17110 as a prerequisite of W6636. Preflight Docker and the
   operator's read-only credential providers without exposing secrets.
2. [pending] Build and run a spike-only Claude container. Deliver a correlated
   `ping` through the smallest practical native/ACP wrapper, collect `pong`,
   retain redacted evidence and prove cleanup.
3. [pending after Claude evidence] Build and run a spike-only Codex container
   with the same outer input/result/cleanup shape. Deliver the correlated
   `ping`, collect `pong`, retain redacted evidence and prove cleanup.
4. [pending] Compare the two trials at the wrapper boundary: packaging,
   authentication method, startup, request/result transport, failure behavior,
   teardown and what can remain runtime-neutral in v12.
5. [pending] Return for independent review. Both agents must have executed
   inside Docker and returned the correlated pong for satisfying closure; do
   not represent the spike as production conformance.

## Progress — 2026-08-27

1. [done] Preflight. Docker 29.1.3, container egress to both providers proved
   from inside a container. **The nominated credential provider is absent.**
2. [done as far as credentials allow] Claude spike image built and run: real
   runtime, read-only input, correlation carried, `output.json` last, positive
   cleanup. Reaches its **authentication** boundary and records it redacted.
3. [done as far as credentials allow] Codex spike image built and run through
   the same outer shape, with the same result and its own distinct wrapper
   behaviour.
4. [done] The wrapper-boundary comparison: packaging, credential-mount shape,
   home-directory constraints, image-time ownership, failure behaviour and
   teardown. Recorded, including what it means for W6634's read-only
   credential delivery.
5. [blocked on one operator decision] Both trials return the correlated pong.
   Needs a nominated credential provider; `trial.py --credentials` takes it.

## Independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T04-25-44Z.md`.

1. [next P0] Replace raw provider stdout/stderr in result and durable host
   output with a strict allowlist: exact pong/correlation on success, or a
   closed redacted failure category plus bounded operational facts. Keep the
   additive arbitrary-output regression.
2. [next P1] Make the host prove exact textual `pong`, zero exit, expected
   provider/spike identity, matching correlation and the closed result shape;
   do not trust the worker-authored boolean. Keep the nonzero/malformed case.
3. [next P1] Enforce image/container cleanup results, query immutable image
   identity after removal, and include staged-root absence in `clean` and
   `satisfying`. Keep both cleanup regressions.
4. [next] Make preflight distinguish a present credential path from one the
   configured uid 65532 can read. Do not use the operator's `1000:1000 0600`
   personal files without an explicit new ruling.
5. [blocked after correction] Obtain an operator-nominated readable provider,
   rerun Claude then Codex, and return exact category/pong and cleanup evidence.
   Satisfying closure still requires both real agents' correlated exact pong.

## Correction — 2026-08-27, after independent review

- [done] Durable output is an allowlist of computed facts. No provider text
  reaches a result, an evidence file or a log; the answer crosses as a digest
  so the host can decide an exact match without seeing it.
- [done] The host recomputes the verdict — spike, provider, correlation, both
  exit states and an exact-digest answer — rather than trusting the document.
- [done] Every cleanup result is enforced and included in the verdict; the
  image is queried by immutable id when its removal failed.
- [done] Preflight distinguishes present from readable-by-the-container-uid,
  without opening a credential.
- [blocked, unchanged] Both trials return the correlated exact pong. Needs an
  operator-nominated provider readable by uid 65532, or a ruling giving the
  container a different identity.

## Second independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T04-37-23Z.md`.

1. [done] Accept the original four corrections: provider text excluded from
   the durable host report, exact host-owned verdict, refused image removal and
   surviving staged root all fail closed.
2. [next P1] Refuse unknown, extra or missing members against the exact
   published success/failure shape; allowlisting remains the report-copy
   boundary, not document validation.
3. [next P1] Include `docker ps` and `docker image ls` query status, plus
   timeout kill/removal outcomes, in the cleanup verdict.
4. [next P1] Gate preflight READY on the nominated provider's readability by
   uid 65532. A directory provider needs read and execute on itself and execute
   on every ancestor; assess the exact provider-specific mount path.
5. [next] Keep all nine additive cases and make them green before any live
   credential is mounted. The operator nomination and two real pongs remain
   the final separate gate.

## Correction — 2026-08-27, after the re-review

- [done] The published document is validated against one exact closed shape
  before the verdict is derived; filtering stays the durable-report boundary.
- [done] Every cleanup query's status participates in the clean verdict, and
  so does the timeout path's kill and removal.
- [done] Preflight gates readiness on readability, requires read AND execute on
  a directory provider plus execute on every ancestor, and assesses the exact
  paths each trial mounts.
- [done] Four guards that measured vacuous are separated by their own cases in
  `v12/spike/ping-pong/test_harness.py`.
- [blocked, unchanged] Both trials return the correlated exact pong.

## Third independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T04-45-37Z.md`.

1. [done] Accept exact member-set refusal, cleanup/query enforcement, timeout
   cleanup enforcement, nominated-root readability and directory traversal.
2. [next P1] Validate every published fact's bounded type/grammar and make the
   success/failure result shapes exclusive; an exact successful pong cannot
   carry a failure category.
3. [next P1] Gate READY on both exact provider-specific paths, not only the
   generic nominated root. Support another layout only through explicit paths.
4. [next] Keep all twelve reviewer cases and six separation/control cases
   green. Then request an operator-nominated readable provider and run both
   real exact-pong trials.

## Correction — 2026-08-27, after the third review

- [done] Every required published fact is held to its own bounded rule, and the
  success and failure shapes are exclusive.
- [done] Readiness requires every exact path a trial mounts, not the root alone;
  the report is printed after the verdict is computed.
- [done] Three further guards that measured vacuous are separated by their own
  cases, with controls.
- [blocked, unchanged] Both trials return the correlated exact pong.

## Fourth independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T04-55-30Z.md`.

1. [done] Accept bounded fact rules, exclusive success/failure shapes and the
   exact per-provider readiness gate.
2. [next P1] Make every fact predicate total over arbitrary JSON values; an
   array-valued provider must refuse the shape rather than raise.
3. [next P1] Query the recorded immutable image identity after every tag
   removal. A surviving identity prevents `clean`, including when untagging
   returned zero.
4. [next] Keep all fourteen reviewer cases and twelve separation/control cases
   green, then request an operator-nominated readable provider and run both
   real exact-pong trials.

## Correction — 2026-08-27, after the fourth review

- [done] `_closed_shape` is total over arbitrary JSON: per-rule type guards,
  and a blanket for a rule that raises, each established separately.
- [done] Image absence is proved by the recorded identity after every removal
  attempt, not by a query on the tag that was just removed.
- [blocked, unchanged] Both trials return the correlated exact pong.

## Fifth independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T05-04-38Z.md`.

1. [done] Accept the total provider-value validator and recorded-identity
   survivor check.
2. [next P1] Distinguish a successful proof of image absence from an identity
   query execution failure; record the real status and require it in `clean`.
3. [next] Keep all fifteen reviewer cases and fifteen separation/control cases
   green, then request an operator-nominated readable provider and run both
   real exact-pong trials.

## Correction — 2026-08-27, after the fifth review

- [done] The identity query's outcome is three-valued — present, observed
  absent, or did not run — and the third participates in `clean` rather than
  passing for the second. An absent query (no recorded id) is not a failed one.
- [blocked, unchanged] Both trials return the correlated exact pong.

## Sixth independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T05-12-00Z.md`.

1. [done] Accept status-125 failure handling and inclusion of the identity
   query outcome in `clean`.
2. [next P1] Replace the invented “inspect status 1 means absent” rule with a
   positive, status-bearing absence observation; Docker also uses status 1 for
   daemon-query failure.
3. [next] Keep all sixteen reviewer and sixteen separation/control cases green,
   then request an operator-nominated provider and run both real exact-pong
   trials.

## Correction — 2026-08-27, after the sixth review

- [done] Absence is the engine's own not-found wording rather than an
  exit-status contract this harness invented, narrow enough not to match a
  reachability failure, and pinned in both directions against the real strings.
- [done] A status-bearing inventory is a second witness that may only add a
  survivor, never establish absence.
- [blocked, unchanged] Both trials return the correlated exact pong.

## Seventh independent-review outcome — 2026-08-27

Status: **bounded harness signed off** in
`review-2026-08-27T05-20-04Z.md`.

1. [done] Accept the narrow engine not-found observation plus independent
   full-id survivor inventory. All sixteen reviewer and nineteen separation
   cases pass.
2. [SUPERSEDED 2026-08-27 — done in its first half, and its second half no
   longer exists] Nominate per-provider credentials readable by uid 65532 and
   run Claude then Codex, ~~or explicitly decline/park the live credential
   experiment as a partial non-satisfying result~~. The provider was staged
   and both trials ran; the decline/park option was removed by the full-proof
   ruling. Marked on the line itself because a confirmed decision must leave
   only one actionable rule, and a later section saying so elsewhere still
   left this one readable as live.
3. [satisfying closure only after proof] Require both correlated exact pongs
   and enforced clean teardown. Do not treat harness sign-off as conformance or
   as a satisfying two-provider outcome.

## Live credential trial — approved 2026-08-27

1. [operator] Stage only the Claude and Codex credential files as volatile
   `/run/baton/credentials/{claude,codex}`, owned `65532:65532`, mode `0400`;
   do not alter the personal source files.
2. [impl] Run the signed-off harness without `--keep`, Claude first and Codex
   second. Mount only the provider-specific file read-only; keep runtime state
   private, writable and ephemeral.
3. [impl/review] Record only the closed allowlisted result, exact-pong verdict,
   image/container identity and proved cleanup. Provider text and credential
   material never enter durable output.
4. [operator] After both trials and cleanup proof, unlink the two exact volatile
   files and remove only the empty provider directories.
5. [decision] Close satisfying only for two correlated exact pongs with clean
   teardown; otherwise retain the redacted provider-specific failure as the
   experiment result and decide non-satisfying closure or a narrowly bounded
   follow-up.

## Live preflight correction — 2026-08-27

1. [done, operator evidence] Preserve the approved `0711` carrier and `0400`,
   `65532:65532` exact provider files; both exact entries are reported usable.
2. [next, impl] Make readiness distinguish an exact-file carrier from a
   directory provider. In exact-file mode, require traversal through the
   carrier and readability of each exact file, not permission to list the
   carrier.
3. [next, impl] Add positive coverage for a `0711` carrier with both `0400`
   exact files and negative coverage for a non-traversable ancestor. Retain all
   signed-off preflight and cleanup regressions.
4. [then] Re-run preflight. Only after it reports `READY`, run Claude and then
   Codex without `--keep` under the approved exposure boundary.

### Access-probe ruling — 2026-08-27

- [approved for W17110] An isolated probe may read and discard exactly one
  credential byte to establish effective container access across engine UID
  mapping. It emits and retains no credential-derived material. Do not delay
  the live trial to replace this with a purely metadata-based probe.

## 2026-08-27 — the remaining step

- [done] Independent sign-off on the bounded harness (seventh review).
- [done] `v12/spike/ping-pong/OPERATOR.md`: the exact commands for either
  operator answer, including why the operator's own credential files cannot be
  mounted as they stand.
- [SUPERSEDED 2026-08-27] Nominate providers readable by uid 65532 and run
  both trials, ~~or decline and close/park as a partial result~~. Done in its
  first half; the decline option was removed by the full-proof ruling.

## 2026-08-27 — the first credentialled trials

- [done] Readability is observed by a probe container rather than modelled from
  host-side ownership; readiness is about the exact paths each trial mounts,
  not the listability of the root above them. Two rules of my own corrected.
- [done] Both trials run against the operator's nominated provider, in the
  ruling's order, with results classified and no provider text recorded.
- [operator decision] Claude: re-copy from a freshly refreshed host credential
  (preserves the read-only constraint), or revise the constraint to permit a
  writable credential mount for OAuth-refreshing runtimes.
- [open] Codex: the backend connection failure is undiagnosed.

## Closure supersession — 2026-08-27

- [superseded] Do not close or park W17110 merely because the bounded harness
  produced useful categorized failures.
- [required] Correct the Claude credential-refresh path and the Codex network
  path, then repeat the bounded live trials.
- [closure gate] Keep W17110 open until both real providers return their
  correlated exact `pong` and the host proves clean teardown for each.

## Eighth independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T13-09-43Z.md`.

1. [done] Accept the ordered real trials, their closed non-satisfying reports
   and proved clean teardown.
2. [next P1] Require both carrier/ancestor traversal and a successful empirical
   exact-file readability observation. A failed probe concludes nothing and
   never falls back to READY.
3. [next P1] Replace the causal `credential-refresh-blocked` claim unless a
   fixed write-denied signal is observed. Record Claude as an expired/refresh-
   related authentication result and Codex as network; do not claim either
   proves exact-file read-only delivery insufficient.
4. [next P1] Append an explicit no-provider-text evidence correction without
   reproducing the raw wording. Replace recursive cleanup in `OPERATOR.md` with
   exact unlink and empty-directory removal.
5. [then] Correct the Claude and Codex paths and repeat the bounded live trials.
   Satisfying closure remains two correlated exact pongs plus clean teardown.

## Correction — 2026-08-27, after the eighth review

- [done] Ancestor traversal and observed exact-file readability are independent
  readiness gates; a failed probe cannot fall back to the host-side model.
- [done] The Claude diagnosis is `credential-expired` (descriptive);
  `credential-write-denied` is a separate category earned only by a
  write-denied signal. The W6634 takeaway separates confirmed facts from
  hypotheses.
- [done] The provider-text breach in the previous evidence is corrected
  alongside it rather than silently rewritten.
- [done] `OPERATOR.md` uses the approved exact `unlink`/`rmdir` cleanup and no
  longer offers the superseded partial-closure path.
- [open] Both trials return the correlated exact pong: Claude needs a token
  inside its lifetime, Codex needs its connection failure diagnosed.

## Ninth independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T13-21-40Z.md`.

1. [done] Accept the two independent preflight gates, failed-probe fail-closed
   behavior, explicit evidence correction and exact cleanup instructions; keep
   all eighteen reviewer and twenty separation cases green.
2. [next P1] Do not call a generic permission/write failure
   `credential-write-denied`. Use a descriptive category unless the fixed
   signal identifies the credential mount, and add category controls.
3. [next P1] Update `OPERATOR.md` to the current staged-provider state and mark
   the old PLAN decline/partial-close action itself superseded.
4. [next P2] Correct the new transcript's repository-mutation statement to the
   narrower fact actually established.
5. [then] Run the operator-designated authoritative Claude trial against the
   freshly renewed staged credential and continue the bounded Codex diagnosis.
   Close only after both correlated exact pongs and clean teardown.

## 2026-08-27 — the proof

- [done] The ninth review's three findings: causation earned only by a signal
  naming the mounted credential path (with controls, which found an ordering
  defect); operator documents brought to the current state and the superseded
  action marked on its own line; the mutation claim narrowed to the fact.
- [done] Codex's `network` failures diagnosed: the image carried no CA
  certificate bundle, and a native-binary runtime uses the system trust store.
  Installed on both images.
- [DONE — the closure condition] Both a real Claude container and a real Codex
  container returned the correlated exact `pong` through the approved
  input/output boundary, with enforced clean teardown, in one run each.
- [operator] Unlink the two exact volatile entries and remove the now-empty
  provider directories, per the approved decision and `OPERATOR.md`.

## Tenth independent-review correction — 2026-08-27

Status: **changes requested** in `review-2026-08-27T13-36-53Z.md`.

1. [done] Accept the credible two-success summary, CA bundle correction and
   green 18+24 regression gates.
2. [next P1] Attach the exact provider-text-free stdout JSON reports from both
   successful trials, including correlation/digest/exit/closed-shape and all
   cleanup query outcomes; rerun if the originals were not retained.
3. [next P1] Make credential-causation matching diagnostic-local or use the
   conservative write-denied category; add a cross-line negative control.
4. [next P1] Update `OPERATOR.md` to the post-proof state.
5. [then review] Independently sign off the exact two-pong proof.
6. [then operator] Unlink the two exact staged credential entries, remove only
   empty provider directories, confirm withdrawal, and close satisfying.

## 2026-08-27 — the tenth review

- [done] Both successful trials rerun and their exact `trial.py` stdout
  persisted verbatim, so correlation, digest, exit states, publication shape,
  completion signal, image identity and every cleanup outcome are recomputable
  from the record rather than asserted in prose.
- [done] Write-denied causation requires the denial and the credential path in
  the same diagnostic, with cross-line negative controls and a positive.
- [done] `OPERATOR.md` names the one remaining operator action.
- [operator, then closure] Unlink the two exact volatile entries and remove the
  now-empty provider directories; terminal closure follows that confirmation.

## Eleventh independent-review signoff — 2026-08-27

1. [done] Recompute both exact reports: distinct carried correlations, exact
   pong digests, both exit layers zero, closed publications, full image ids,
   status-bearing clean teardown and satisfying verdicts.
2. [done] Retain all eighteen reviewer and twenty-six separation cases green;
   verify diagnostic-local classification and post-proof operator state.
3. [signed off] Both real-provider correlated exact pongs and clean teardown
   discharge the proof gate.
4. [operator] Unlink only `/run/baton/credentials/claude` and
   `/run/baton/credentials/codex`, remove only empty provider directories,
   confirm withdrawal, and close W17110 satisfying.

## Private-development retention supersession — 2026-08-27

1. [superseded] Credential withdrawal is no longer a W17110 closure gate on
   this private development box.
2. [done] Both real-provider exact-pong reports independently recompute as
   satisfying, focused gates pass, and both trial containers and images were
   removed cleanly.
3. [confirmed] Retain the two exact owner-only files under
   `/run/baton/credentials/` as volatile operator-managed fixtures for future
   explicit trials; keep them outside images and every Baton durable surface.
4. [next] Close W17110 satisfying. Future trials re-run preflight and refresh
   or restage any expired credential before use.
