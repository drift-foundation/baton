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
