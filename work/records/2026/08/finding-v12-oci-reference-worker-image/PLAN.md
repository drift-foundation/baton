# Plan: OCI reference worker image

1. [implementation-ready] Pin the image/base digest, scripted M2 agent and
   posture-specific worker entry contract.
2. [pending] Implement `baton-worker` and its protected framed channel.
3. [pending] Build consent and execution postures without session promotion or
   pre-mounted future capability.
4. [pending] Add reproducibility, inspection, protocol and isolation tests.
5. [pending] Record focused evidence and return for independent review.

## Review correction — 2026-08-24

Status: **changes requested** in
`review-2026-08-24T23-52-15Z.md`.

1. [done — decision 2026-08-25] Use closed per-operation request/response
   shapes with exact posture-session and one-use operation identity on every
   frame; exclusive stdio alone is not the binding. Cancellation remains the
   manager's explicit runtime control path, not clean EOF or a worker-entry
   operation.
2. [required] Own each whole request before dispatch so assignment, workspace,
   output or other unexpected material cannot enter a consent process through
   a frame.
3. [required] Convert invalid/missing startup posture into one bounded fault
   frame and non-zero exit without an uncaught traceback.
4. [required] Define and exercise an actual cancellation path; an input stream
   empty from its first byte is not evidence of intentional cancellation.
5. [required] Build the pinned-platform image, record/prove reproducible image
   identity, inspect actual config/layers/filesystem posture, run real consent
   and execution negative cases and prove every engine resource absent.
6. [verification] Make the additive reviewer cases green, then run focused,
   image/container, full source and locked installed-layout gates before
   returning for independent review.

## Re-review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T03-09-10Z.md`.

1. [done] Refuse unexpected consent-frame material and frame invalid startup
   posture without a traceback; the two first-round additive cases are green.
2. [required] Implement the approved common protocol/session/operation
   identity, exact per-operation request sets, one-use replay fence, echoed
   response identity, and closed answer-object validation.
3. [done — decision 2026-08-25] Latch entrypoint/bootstrap faults while the
   framing loop remains operable, read exactly one bounded request identity
   envelope, and return the normal correlated fault before non-zero exit;
   never dispatch the task or expose capability after the fault. If the
   framing loop itself cannot start, the Worker Manager settles its already
   identified operation as `worker_start_failed`; do not add an uncorrelated
   worker response shape.
4. [required] Replace initial clean EOF as the cancellation fixture with the
   manager's real container stop/termination path and observable settlement.
5. [required] Deliver a self-cleaning pinned-platform build/inspect/run gate;
   record the actual image/config/layer/filesystem/user/capability posture and
   real consent/execution negative evidence.
6. [verification] Run the corrected focused and image/container gates, then
   the full source and locked installed-layout gates before re-review.

## Re-review correction landed — 2026-08-25

Status: **corrected and verified; awaiting final review.**

2. [done] The approved common identity, exact per-operation request sets, the
   one-use replay fence, the echoed response identity and closed answer-object
   validation are implemented; wrong-session, cross-posture-session, missing,
   unknown, extra-member and replay cases all drive them.
4. [done] Cancellation is the manager's real container stop path with its
   settlement recorded; the superseded clean-EOF fixture now says what it
   actually observes and why it cannot stand in for a stop.
5. [done] A self-cleaning pinned-platform build/inspect/run gate,
   `tests/manager/test_worker_container.py`, 21 cases: engine-applied config,
   layer filesystem read from inside a container, real consent/execution
   negatives, and two cases asking the engine whether anything survived. It
   FAILS rather than skips without a daemon.
6. [done] Focused 54/54, image/container 21/21, full source and locked
   installed-layout runs recorded in `evidence/gate-after-2026-08-25.txt`.

## Final re-review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T07-19-30Z.md`; the preceding awaiting-review status is
superseded.

1. [done 2026-08-25] Preserve the common protocol and expected-session checks on the
   latched startup-fault path before returning the pending correlated fault;
   make the additive wrong-session bootstrap regression green without
   dispatching an agent or reading a second frame.
2. [done 2026-08-25] Build the image independently for one explicit platform,
   inspect the applied OS/architecture, compare immutable image identities,
   and clean both tags on every path.
3. [done 2026-08-25] Correct the residual-container assertion so every non-empty
   suite-prefixed Docker result fails it; the current predicate discards every
   container the suite could have left behind.
4. [done 2026-08-25] Run the corrected focused and daemon-backed gates and
   append their exact outcomes before returning for independent review.

## What the three corrections actually changed — 2026-08-25

**1. The binding is `bind`, and it holds on every path.** The protocol and
expected-session checks lived inside `handle`, which the latched bootstrap
path never reaches — so a container that had failed to start echoed an
arbitrary peer's session and disclosed its own posture failure to whoever
asked. Startup correlation supplies an operation identity; it does not suspend
the binding. The two checks are lifted into `bind`, and `serve` establishes
the correlation immediately after the one bounded identity envelope, BEFORE it
decides whether to answer with the latched fault or dispatch. `handle` keeps
entitlement, shape and the replay fence and no longer takes `expected`.

The three properties the correction had to keep are now pinned by cases of
their own rather than inferred: a latched container writes EXACTLY ONE frame
and exits non-zero whichever fault it names; no agent method is reachable on
that path; and a healthy container's ordinary wrong-session refusal still does
NOT end the channel — only a latched one stops.

**2. The platform is named and the identity is reproduced.** The build
selected no platform, so nothing could say which platform the recorded
identity belonged to, and `test_the_image_has_one_identity_and_it_is_a_digest`
proved only that one build's id had digest syntax. The gate now builds with an
explicit `--platform`, taken from the engine's own server so it runs on arm64
without demanding emulation and is passed explicitly so what was ASKED FOR and
what was APPLIED are two facts that can disagree. The same context is then
built a second time under its own tag and the immutable identities compared.

The claim is made narrowly on purpose: this recipe is a pinned base plus two
`COPY`s and metadata, with deliberately no package manager and no network
client, which is what makes a same-identity claim available at all. A recipe
that installed anything could not make it — and if one is ever added, this is
the case that says so.

**3. The residual assertion can now fail.** It filtered for names containing
`baton-w6633-test` and then discarded every name STARTING with
`baton-w6633-test-`, which is the prefix every container this suite makes. The
list was empty whatever survived. It asserts over every non-empty match now,
and a companion case creates a real container and requires the same question
to come back naming it — a guard with nothing to catch changes no verdict, so
it is handed something. Both image tags are registered for removal before
either build can create one, and the tag sweep allows exactly this run's two.

## Fourth review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T09-47-54Z.md`.

1. [done 2026-08-25] Confirm the prior three corrections and the 58/58 focused
   worker gate.
2. [next] Apply the adapter's complete unconditional `RESTRICTIONS` posture to
   every real channel, inspection and cancellation container in the daemon
   gate. Keep the derived argv regression and observe effective capability and
   root-filesystem posture inside the resulting container.
3. [next] Make the second explicit-platform build cache-independent (for
   example with an isolated/disabled builder cache) before comparing immutable
   identities. Keep the additive cache-isolation regression.
4. [next] Run the corrected focused and daemon-backed gates, prove engine
   cleanup after the run, append exact evidence, and return for review.

## Fourth review correction — 2026-08-25

`review-2026-08-25T09-47-54Z.md` confirmed the three final-review corrections
and found two source-visible defects in the daemon gate. Both are fixed and
both of its additive daemon-free regressions are green and kept as written.

1. [done] **[P1] The daemon gate launches what the manager launches.**
   `restricted(*flags)` is derived from `worker_manager.oci.RESTRICTIONS` and
   applied to the channel, the filesystem inspection, both cancellation starts
   and the new probes. Derived rather than retyped, so a restriction added to
   the adapter is applied here without anyone remembering to. Module-level, so
   the reviewer's duck-typed harness reaches it.

   And because argv says only what was ASKED FOR, three cases read the
   applied posture from inside a running container: every capability set empty
   with `NoNewPrivs` set, `/` and `/opt/baton` unwritable while the named
   tmpfs is writable, and both tmpfs mounts carrying `noexec,nosuid,nodev` in
   `/proc/self/mounts`.
2. [done] **[P1] The rebuild is an execution, not a cache hit.** `--no-cache`
   is unconditional rather than a keyword a caller may relax — the adapter's
   own reasoning about its restrictions, applied to this gate.
3. [done — WITH A DISAGREEMENT, recorded] The review asked to compare
   immutable identities after cache isolation. Measured on docker 29.1.3: the
   image ID is the digest of a config carrying a wall-clock `Created`, so two
   independent builds have two ids by construction, while all six RootFS
   layers are identical. `SOURCE_DATE_EPOCH` does not change it and this host
   has no `buildx`. The case therefore compares the ARTEFACT — every layer
   digest and the applied configuration — and a companion case holds the
   measurement, so the claim is checked rather than believed and a future
   engine with reproducible ids makes that case fail rather than passing
   quietly. The measurement and the offer to invert it are in
   `evidence/gate-after-fourth-correction-2026-08-25.txt`.

## Fifth review correction — 2026-08-25

Status: **changes requested** in
`review-2026-08-25T12-19-50Z.md`.

1. [done] Confirm the full manager restriction table reaches every daemon-gate
   launch, its key effects are observed inside the container, every build is
   cache-independent, and the daemon-free focused gate is 60/60 green.
2. [next] Produce one deterministic OCI image identity from two independent
   builds for the pinned platform, not only equal RootFS layer digests and a
   selected config subset. Keep the additive image-ID regression.
3. [decision if item 2 is intentionally unsupported] Obtain and append an
   explicit approver supersession of the confirmed reproducible immutable
   image-digest acceptance. Until then the gate fails unsupported; the test
   requiring unequal image IDs cannot stand as certification.
4. [next] Run the corrected daemon-backed gate and record the exact immutable
   identity, platform and post-run cleanup before returning for review.

## Fifth review correction — 2026-08-25

`review-2026-08-25T12-19-50Z.md`'s one [P1] is corrected by satisfying the
acceptance rather than by superseding it.

1. [done] **The recipe has a deterministic output step.**
   `v12/python/tools/worker_image.py` normalizes the build's receipt metadata
   and loads the result back; two independent executions reach one image
   digest, which an operator can produce with
   `python3 -m tools.worker_image --tag …`. Pinned in `FINDING.md`.
2. [done] **The record's measurement is corrected.** The layers are volatile
   too — the `COPY` layers carry the build-clock mtime of the directories the
   copy created — and the earlier "layers identical" reading was two builds
   landing inside one wall-clock second. This also explains the previously
   unattributed full-run interaction.
3. [done] **The review's additive regression passes as written.**
   `test_two_independent_builds_have_one_pinnable_image_identity` is kept
   untouched.
4. [done] **The weakening is withdrawn, not the fact underneath it.**
   `test_the_image_id_is_a_receipt_and_not_the_artefact` required the two
   identities to stay different and is replaced by
   `test_a_bare_engine_build_is_why_the_output_step_exists`, which requires a
   bare build to be irreproducible in both id and layers and then requires the
   output step to make one identity of it.
5. [done] **The rule has a daemon-free gate.**
   `tests/tools/test_worker_image_build.py`, 18 cases over a layout it writes
   itself, including both degenerate base classifications and the other half —
   two layouts differing in their PROGRAM still reach two identities.
6. [done] **One defect of this correction's own, caught by the suite's own
   sweep.** Moving the build into the tool left the cache case patching a
   helper it no longer reached, so it ran a real build and leaked its tag. It
   reads a golden `build_vector` now.
7. [done] Focused `test_worker_image` 58, `test_worker_image_build` 18,
   daemon-backed `test_worker_container` 31 against docker 29.1.3; full source
   suite and locked installed-layout build both 1210 with ten failures, none of
   them this correction's.
8. [next] Independent review.

## Sixth review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T00-41-16Z.md`.

1. [next] Preserve the pinned base's ordered diff-id sequence and require it
   to be the built image's exact prefix before rewriting any suffix layer.
   Refuse partial, reordered, missing or interleaved base ancestry. Keep the
   additive partial-match regression.
2. [next] Allocate a distinct staging reference per build invocation, pass
   that exact reference through build/save/cleanup, and prove that one build's
   cleanup cannot remove another build's unnormalized image. Keep the additive
   same-destination concurrency regression.
3. [next] Re-run the daemon-free worker/image/runner gates, then the isolated
   daemon-backed gate and its positive engine cleanup checks. Record the exact
   normalized identity and return for independent review.


## Sixth review correction — 2026-08-26

Both findings in `review-2026-08-26T00-41-16Z.md` are corrected and both
additive methods are green.

1. [done] **[P1] Ancestry is an ordered prefix.** The base's diff ids are an
   ordered sequence and the built image must begin with that exact sequence,
   with at least one recipe-owned suffix layer. The recipe's layers are the
   suffix taken by position.
2. [done] **[P1] The stage is allocated per invocation** and threaded through
   build, save and cleanup; `build_vector` takes it as an operand.
3. [done] Fixtures that passed the base layers as a set now pass an ordered
   sequence, because a set would have made those cases depend on iteration
   order once ancestry became a prefix. No assertion changed.
4. [done] `test_worker_image_build` 18 -> 22; both corrections measured to
   fail without them, the ancestry one re-measured after a first revert that
   was not faithful and proved nothing.
5. [done] Daemon-backed gate 31/31 against docker 29.1.3, with no staging
   image surviving the run; `test_parallel_runner` 36 OK.
6. [done] Source suite and locked build both 1232 with eleven failures, and
   `tests.tools.test_worker_image_build` is not among them.
7. [next] Independent review. PLAN item 6's deploy and the W12181 smoke remain
   the operator's.

## Seventh review correction — 2026-08-26

Status: **changes requested** in
`review-2026-08-26T02-37-11Z.md`.

1. [next P1] Remove ambient source-checkout mtimes from every recipe-owned
   layer member, while preserving source bytes, modes, link targets and other
   semantic filesystem content. Keep the additive two-checkout-mtime
   regression.
2. [next] Revise
   `test_a_file_keeps_the_mtime_it_came_in_with`, which pins the defect, to the
   reproducible member-time contract. This is explicit case-specific
   confirmation to change that unsafe expectation.
3. [next P1] Check the per-invocation staging-image removal result. A refused
   removal must prevent a successful identity return; preserve any earlier
   build failure while reporting the cleanup failure actionably. Keep the
   additive failed-removal regression.
4. [next] Re-run the daemon-free worker/image/runner gates, then the isolated
   daemon-backed build/inspect/container gate and its positive cleanup checks.
   Record exact evidence and return for independent review.


## Seventh review correction — 2026-08-26

Both findings in `review-2026-08-26T02-37-11Z.md` are corrected.

1. [done] **Every member time in a recipe-owned layer is normalized**, not
   only directory entries. The mtime half of the output-step decision is
   explicitly SUPERSEDED in `FINDING.md` with its reasoning.
2. [done] **A refused staging removal fails the build**, with the raise after
   the `finally` so an earlier failure stays primary.
3. [done] The file-mtime assertion is revised under the review's explicit
   confirmation, and its class renamed from
   `InsideTheRewrittenLayerOnlyDirectoryTimesMove` to
   `InsideTheRewrittenLayerOnlyTheClockMoves`.
4. [done] `test_worker_image_build` 22 -> 27; both corrections measured to
   fail without them.
5. [done] Daemon-backed 31/31 against docker 29.1.3 with no staging image
   surviving; `test_worker_image` and `test_parallel_runner` 94 OK.
6. [done] Source suite and locked build both 1253 with SEVEN failures, taken
   back to back over a tree hashed identical before and after — and the seven
   are the long-standing boundary-inventory ones and nothing else.
7. [next] Independent review. PLAN item 6's deploy and the W12181 smoke remain
   the operator's.

## Eighth review correction — 2026-08-26

Status: **changes requested and contract-blocked** in
`review-2026-08-26T04-26-30Z.md`.

1. [blocked on `W14251`] Complete the prerequisite artifact-neutral worker-
   control and conformance-contract revision ordered by
   `work/records/2026/08/finding-v12-isolated-agent-workers/PLAN.md`. Do not
   continue certifying the superseded inline-task/environment protocol while
   that prerequisite remains open.
2. [next] Revalidate this whole record against the revised contract, then make
   the reference image consume read-only `/input/input.json` plus declared
   payloads, use writable `/output` and private ephemeral space, and publish
   `/output/output.json` last. Remove obsolete inline `task`, assignment,
   workspace and output-environment semantics rather than translating them in
   the host manager.
3. [next P1] Preserve an earlier build exception across every staging-removal
   outcome. Attach actionable cleanup evidence when removal returns nonzero or
   raises; when no earlier failure exists, either cleanup form remains the
   build's own failure. Keep both additive earlier-failure regressions.
4. [next] Rerun the daemon-free worker/image/runner gates, the isolated
   daemon-backed gate and its positive cleanup checks after the prerequisite
   contract has landed. Record exact evidence and return for independent
   review.


## Ninth round — 2026-08-26

[done] The [P1] cleanup correction: `_cleaned_up` answers rather than raises,
an earlier failure keeps primacy and carries the cleanup outcome as a note, a
cleanup that could not run is evidence rather than a new primary, and either
outcome on the successful path is still a failure. Three guards, each measured
by removal. 29/29.

[done] The blocker is revalidated as LIFTED: W14251 is closed and W6633 reports
zero open blockers. The pinned contract and the exact six-point change this
image needs are recorded in `PROGRESS.md`, measured against the current worker
rather than restated from the review.

[next] Implement the artifact-neutral worker I/O as its own slice: the worker
protocol, the scripted agent, and both image suites.

## Ninth independent review — 2026-08-26

Status: **changes requested; prerequisite lifted** in
`review-2026-08-26T21-11-48Z.md`.

1. [done] Accept the eighth review's cleanup correction. Preserve the primary
   build failure, attach bounded cleanup evidence to it, and fail an otherwise
   successful build when cleanup returns nonzero or raises. The three
   regressions and the 123-case daemon-free worker/image/runner gate are green.
2. [next] Replace the inline-task `work` request with a common-envelope-only
   request. Read and validate `/input/input.json` inside the execution worker,
   including its expected assignment/session binding, before the agent runs.
3. [next] Remove `BATON_WORKER_ASSIGNMENT`, `BATON_WORKER_WORKSPACE`, and
   `BATON_WORKER_OUTPUT` from the execution environment. Retain the common
   consent environment, posture boundary, identity binding, replay fence,
   framing, and bounded refusal behavior.
4. [next] Make the scripted agent return only disposition, recap, and produced
   output names. The worker, not the agent, validates those names against the
   closed declarations, measures `/output` content, and authors the complete
   W14251 completion manifest.
5. [next] Publish `/output/output.json` last and atomically by same-directory
   rename. Prove no manifest becomes visible for malformed input, undeclared
   or missing required output, agent refusal/failure, measurement failure,
   interruption, or partial writes.
6. [next] Change the correlated work answer to exactly `disposition`,
   `outputs`, and `recap`, with `outputs` a bounded list of names and no
   workspace or host path. Prove ephemeral material is excluded unless copied
   beneath a declared output before completion.
7. [confirmed test authority] Revise existing assertions that require inline
   `task`, the `workspace` answer, or any of the three obsolete environment
   members: W14251 explicitly supersedes those expectations. This is
   case-specific confirmation for those tests only. Do not weaken common
   identity, consent isolation, replay, framing, fault, cancellation,
   reproducibility, ancestry, staging-cleanup, or image-identity assertions.
8. [next] Cover direct worker, built-image, and daemon-backed container paths,
   including read-only `/input`, writable `/output`, private ephemeral space,
   exact manifest bytes/content, atomic-last publication, negative/path/race/
   interruption cases, and absence of the old variables. Re-run the
   daemon-free worker/image/runner gates and the isolated daemon-backed gate;
   return exact evidence for independent review.


## Tenth round — 2026-08-26

[done] The artifact-neutral worker protocol: no inline task, no `workspace`
answer, the three environment members removed, `/input/input.json` read,
declared outputs measured by the worker, the agent's answers held against the
declarations, and `/output/output.json` published last and atomically. No
compatibility aliases.

[NOT DONE] `tests/manager/test_worker_image.py` is partly migrated and RED at
52/58; `tests/manager/test_worker_container.py` is untouched and unrun. Six
cases need `staged()` placed correctly on the paths that drive `work` end to
end.

## Tenth independent review — 2026-08-26

Status: **changes requested; blocked on `W19784`** in
`review-2026-08-26T22-31-32Z.md`.

1. [blocked on `W19784`] Resolve and pin the one canonical way the execution
   worker receives the complete assignment identity required to author a
   `completionManifest`. Do not invent `assignment_ref` inside the existing
   W14251 `inputManifest`, revive an opaque environment alias, or create two
   competing identity sources.
2. [next after `W19784`] Consume and validate the resulting canonical input
   contract before agent dispatch. Enforce the closed output declarations,
   safe relative paths, required outputs, and per-output entry/byte constraints
   before publishing completion.
3. [next] Keep the correlated `work` answer at exactly `disposition`, `outputs`,
   and `recap`, but make `outputs` the bounded list of output names. Complete
   output records belong only in the worker-authored completion manifest.
4. [next, existing authority] Finish migrating the six stale inline-task and
   workspace-answer cases under the ninth review's explicit test authority.
   Preserve the existing identity, replay, framing, cancellation, fault,
   consent, image, and cleanup assertions.
5. [next] Make the full direct worker suite green, then update and run the
   daemon-backed container suite against the built image. Prove actual mount
   modes, private ephemeral isolation, removal of obsolete variables,
   canonical input acceptance, exact name-only response, limits enforcement,
   and atomic-last/no-failure publication. Return exact commands and results.

## W19784 ruling — 2026-08-26

1. [approved; blocked until W19784 implements] Use the complete
   `assignmentManifest` at fixed read-only `/input/assignment.json` as the only
   assignment-identity source. Keep `/input/input.json` unchanged, and accept
   no environment, frame or compatibility alias.
2. [next in W19784] Validate both documents and their digest/work/contract/
   policy/profile bindings before agent dispatch. Copy completion identity
   only from `assignment.json`; refuse missing, stale, mismatched or malformed
   assignment material without publishing completion.
3. [still live] Complete tenth-review items 2–5 for declaration enforcement,
   name-only correlated output, stale-test migration and built-container proof.

## Eleventh independent review — 2026-08-27

Status: **changes requested; W19784 dependency satisfied** in
`review-2026-08-27T02-43-39Z.md`.

1. [done] Accept W19784's canonical `/input/assignment.json` delivery and the
   worker's closed-document, self-digest and cross-binding validation. The
   complete delivered assignment identity now reaches the completion envelope.
2. [next P1] Keep complete worker-output records only in `output.json`; return
   only their bounded names in the correlated `work` answer and enforce that
   name-list shape at the final answer boundary.
3. [next P1] Validate the complete closed output descriptor and constraints.
   Enforce required outputs, link policy, entry and byte ceilings during
   measurement, before completion publication or unbounded accumulation.
4. [next P1] Validate normalized relative output paths, canonical containment,
   declaration uniqueness/non-overlap and the reserved `output.json` boundary
   before agent dispatch. Keep the additive private-ephemeral escape case.
5. [next] Make the full direct worker suite green, then add and run built-image
   cases for names-only responses, limit refusal, path containment and
   no-completion-on-failure. Return exact daemon-backed cleanup evidence.

- [done 2026-08-27] The eleventh review's three output-boundary defects, as one
  slice: declarations proved before dispatch against contract-derived rules,
  ceilings enforced while measuring with an account of every other constraint
  member, and the framed answer reduced to bounded names with `check_answer`'s
  exemption removed. Built-container positives and negatives recorded.

## Twelfth independent review — 2026-08-27

Status: **changes requested** in `review-2026-08-27T03-14-22Z.md`.

1. [done] Accept the eleventh-review corrections for names-only framed output,
   entry/byte enforcement, path grammar/containment, overlap, and the reserved
   completion-manifest name.
2. [next P1] Enforce the frozen value types and maxima of every consumed
   output-descriptor and constraint member before agent dispatch. Keep the
   seven additive invalid-value subcases and measure the guards independently.
3. [next P1] Refuse directory symlinks as well as regular-file symlinks during
   output measurement; no link may be silently omitted from the content
   manifest under `link_policy: forbid`.
4. [next] Make the 158-case focused cut green, add built-container negatives
   for invalid consumed values and directory links, rerun the self-cleaning
   41-case Docker gate, and return exact evidence.


## Mandatory operator checkpoint — 2026-08-27

1. [current] K finishes only the already-claimed twelfth-review correction and
   returns exact focused and Docker evidence.
2. [next] Perform one independent review of that correction.
3. [mandatory handoff] After that review, pass W6633 to `baton.ops` whether the
   verdict is clean or changes-requested. Do not route it back to `baton.impl`.
4. [not authorized] No thirteenth correction round until the approver decides
   whether to accept, narrow, split or stop W6633 for the immediate Docker
   proof.

- [done 2026-08-27] The twelfth review's two defects: every consumed
  descriptor and constraint VALUE held to the frozen rule that describes it
  (with an unimplemented keyword a fault rather than a skip), and whole-tree
  link refusal so the "by construction" claim about `link_policy` is true.
  Built-container negatives for an invalid consumed value and a directory
  symlink recorded.

- [done 2026-08-27] Independent checkpoint review accepted both corrections:
  retained regressions 2/2 and complete daemon-free cut 162/162. No new defect
  found; see `review-2026-08-27T03-40-23Z.md`.
- [current] Pass W6633 to `baton.ops` for the mandatory accumulated-scope
  decision. No terminal reviewer sign-off and no thirteenth implementer round
  before the approver accepts, narrows, splits or stops the Work.


## Terminal approver decision — 2026-08-27

1. [done] Accept the checkpoint review and close W6633 satisfying.
2. [owned by W17110] Exercise the reference image through the first live
   Docker ping-pong proof.
3. [owned by W6636] Compose and certify lifecycle, recovery and reconciliation
   behavior outside this Work.
4. [done] Do not begin a thirteenth W6633 correction round. Any newly observed
   failure is separately bounded Work.
