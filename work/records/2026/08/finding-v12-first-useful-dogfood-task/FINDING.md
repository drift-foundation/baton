# Run the first useful v12 dogfood task

## Purpose

Turn the already proven v12 Docker capability into one useful, supervised
development result. A real agent receives a real but low-risk repository task
through the v12 input contract, works only in its isolated container and
output area, and returns a candidate change that an operator can inspect,
test, accept or discard without any mutation of the canonical checkout.

This is the next campaign finish line. It is narrower than the complete M3
proposal platform and more meaningful than another ping-pong: success means
v12 produced reviewable engineering work.

## Confirmed scope — 2026-08-29

The critical path is the smallest honest vertical slice:

1. One documented operator entry point accepts a repository input, a frozen
   task description and the selected real provider.
2. The host-side path is Python and composes the accepted Worker Manager
   authority, reservation/claim, input, launch, execution, output, settlement
   and cleanup seams; it does not create a parallel orchestration model.
3. The exact input is exposed read-only. The worker may copy or clone it into
   private ephemeral space or `/output`, but it never receives a writable
   canonical checkout or Baton's authority store.
4. The first provider is Claude in Docker. The task makes a small, useful,
   independently testable change in a noncritical target selected by the
   operator.
5. `/output/result.json` identifies the assignment and outcome and names the
   candidate artifact. For a Git task the worker may return a candidate commit;
   Git is a workload convention, not Worker Manager protocol vocabulary.
6. The manager collects and seals the result. The operator can inspect the
   candidate diff, run its focused verification and explicitly accept or
   reject it. Nothing automatically merges, stages or mutates the canonical
   repository.
7. Failure is honest: no candidate, mismatched identity, missing result,
   nonzero agent ending, unreadable output or failed verification cannot be
   represented as useful success.

## Explicitly off this milestone's critical path

- Podman certification; W32391 owns that longer-term option.
- Exhaustive negative/race hardening; its existing Jobs remain recorded.
- Generic labels, the v12 TUI, remote workers, multiple coder/reviewer pools,
  automated integration and the complete self-service proposal pipeline.
- Unconditional custody of deliberately hostile worker-selected modes. W36540
  owns that guarantee. This bounded pilot requires its cooperative output to
  be readable, preserves an untrusted attempt when cleanup cannot be proved,
  and never reports that limitation as success.

These exclusions are sequencing, not cancellation. Any observed defect that
can make this positive result false remains a blocker; other hardening is
recorded and proceeds in a later capability pass.

## Scheduling clarification — 2026-08-29

W29400, the low-priority v12 Work-label authority implementation, was already
claimed when this milestone became the explicit campaign focus. It is not a
dependency of W38956 and may finish its current assignment episode. Its
follow-up label work must not occupy the implementation lane ahead of W38956.
Once this milestone is implementation-ready, the next available implementation
claim aims at the useful dogfood result; unrelated expansion remains queued.

## Current-tree revalidation — 2026-08-29

### Confirmed: what W6636 actually proved

The accepted positive lifecycle is real but not yet an operator path. The
production Python seams used by
`v12/python/tests/manager/test_lifecycle_composition.py` compose offer,
reservation, claim, activation, input and launch delivery, OCI start, output
freeze/intake/retention, runtime destruction and positive absence through
`ControlStore`, `AuthorityPort`, `OciAdapter`, `CredentialHome` and the public
Worker Manager operations.

That test deliberately substitutes `FakeSession` for the worker-entry
conversation. Its positive whole-arc case also writes the cooperative worker
output from the host fixture before asking production custody to collect it.
The real-container reference-worker case proves the scripted entrypoint reads
its launch document and exits cleanly on closed stdin; it does not dispatch a
real agent turn. No command under `v12/python/tools/` currently composes the
arc for an operator.

**Consequence:** W38956 must add the smallest production Docker control-stream
bridge needed to drive the already accepted worker-entry frames. Calling the
existing test or writing output host-side would reproduce W6636 evidence, not
satisfy this Work. The bridge remains a runtime-adapter concern: Docker argv,
stdin/stdout and container ids do not enter worker-control protocol vocabulary.

### Confirmed: the current worker is provider-neutral but scripted

`v12/worker/baton_worker.py` accepts an injected agent at `main(agent=...)`,
but its image entrypoint supplies `ScriptedAgent`. `ScriptedAgent` explicitly
is not a provider and deterministically writes fixture output. There is no
production Claude implementation in the worker tree. W17110 proved a real
Claude CLI inside Docker, pinned in `Dockerfile.claude`, but its `trial.mjs`
uses the spike's own prompt/result document and does not speak the
worker-control framing or assignment contract.

**Consequence:** the dogfood worker image may reuse W17110's proven pinned
Claude installation facts, but it needs a provider adapter injected through
`baton_worker.main(agent=...)`. It must not promote `trial.mjs`, its
`w17110-ping-pong` result shape, or the spike's direct Docker lifecycle into
the manager path.

There is one additional positive-composition mismatch to resolve explicitly.
The worker contract fixes output at `/output`, while W6636's lifecycle fixture
mounts its generic writable root at `/workspace` because no real worker writes
there. The real-container worker tests mount the writable output root at
`/output`. W38956 must use the worker's fixed path: mount the assignment
`workspace` root read/write at `/output`, and use bounded container-private
space (the adapter's existing `/tmp` tmpfs) for the agent's editable source
copy. It must not add an unmeasured second writable host root merely to retain
the fixture's `/workspace` spelling.

### Confirmed: source staging belongs outside manager core

W15232 removed Git/source acquisition from Worker Manager core. The manager
receives an already-staged directory; `workspaces.copied_manifest` can copy
and measure that operator-selected tree in one no-follow bounded pass, and
`compose_input_root` finalizes the two manager-authored input documents. The
input manifest records each source destination. The worker itself validates
the two documents and declared outputs but does not copy a source tree into
the writable workspace or pass the source declaration to an agent.

**Consequence:** the operator entry point owns a deliberately external source
stager. For this first task it stages only the nominated task subset, records
its content manifest, and places it at `/input/source` read-only. The provider
adapter copies that exact tree to a bounded private directory below `/tmp`
before invoking Claude.
Neither the manager nor its contracts learn Git vocabulary. The canonical
checkout is never mounted writable and is never the copy destination.

### Confirmed: credential authorization does not transfer from W17110

W17110's permission to use the private development fixture under
`/run/baton/credentials` was explicitly bounded to that spike. W38956 does not
silently inherit it. The existing `CredentialHome` contract can materialize a
named slot and `OciAdapter` mounts it read-only below the fixed
`/run/baton/credentials/` root, with teardown coupled to the runtime ending.

The W38956 command therefore requires an explicit credential source operand
with no home-directory or W17110-fixture default. Its provider callback may
read the nominated file solely to materialize the attempt-scoped `claude`
slot; the secret registry and `EnginePort` remain the owners of leak checks.
The image may provide an image-owned link from Claude's expected credential
location to that fixed slot. It does not copy the bearer into the workspace,
put it in argv/environment/result/evidence, or print/hash/semantically inspect
it. The operator must explicitly authorize the exact credential operand when
running the first trial.

## First useful task — selected 2026-08-29

The first task is an additive regression for the already closed ping-pong
spike, not a change to the dogfood machinery itself:

> Add focused unit coverage for
> `v12/spike/ping-pong/preflight.py::_observed_readable`. Prove the empirical
> probe invokes the nominated engine as uid/gid 65532, with no network, an
> exact read-only bind of the nominated file, and `test -r`; prove readable,
> unreadable, absent-file and nonzero-probe endings remain distinct. Do not
> read credential bytes or weaken the existing readiness rules.

The frozen task and exact three-file source subset are recorded at
`work/records/2026/08/finding-v12-first-useful-dogfood-task/evidence/first-task.md`.

This is useful rather than synthetic: the empirical probe replaced an
incorrect host-uid permission model, yet the current harness tests only
`main()` with `_observed_readable` mocked. No existing test holds the actual
subprocess vector or its result mapping. The target is isolated, currently
clean, additive, independently runnable, and does not overlap the active v12
label or custody implementation files.

Focused verification is:

```text
python3 v12/spike/ping-pong/test_harness.py
```

**Observed baseline, 2026-08-29:** the command passes all 26 current tests in
0.114 seconds without Docker or credential access. Repository search finds no
direct test call to `_observed_readable`; the two `main()` cases patch it with
prebuilt observation documents.

The agent may choose the smallest maintainable cases and names. The candidate
is rejected if it opens credential content, relies on a real Docker daemon or
host credential, changes production probe behavior, weakens an existing
assertion, or only tests the mocked `main()` path.

### 2026-08-30 — approver correction and live-run grants

The earlier three-file delivery is superseded by the same subset plus
`v12/spike/ping-pong/trial.mjs`. The harness reads that sibling in 11 existing
cases; omitting it made the frozen verification command fail before the worker
could contribute. Adding only this fourth read-only source makes the unchanged
command pass all 26 baseline cases and does not change the task objective.

For this private development-box pilot, the exact credential source is
`/run/baton/credentials/claude` and the explicit Docker network posture is
`bridge`. The credential path is an operator input; credential content is
never recorded. These grants are bounded to this supervised trial and do not
become ambient defaults.

**Operational revalidation, 2026-08-31:** the named credential source exists
as a 509-byte regular file at mode `0400`, owned by `nobody:nogroup`, and the
managed repository process running as uid 1000 cannot read it. This was
checked with `stat` and `test -r` only; no credential bytes were opened or
recorded. The grant is pinned, but the live run still waits for an exact source
the operator process may open or an explicit operator-owned permission
correction. The reviewer does not copy, chmod or substitute credential
material.

**Superseding operational verification, 2026-08-31:** the approver corrected
only the external ownership. The same 509-byte regular file remains mode
`0400`, is now owned by `sl:sl`, and `test -r` succeeds as the managed uid
1000 operator. No credential bytes were opened or recorded. The credential
gate is satisfied; the exact path and explicit `bridge` posture remain
unchanged for the one authorized trial.

## Clarified output boundary — 2026-08-29

The earlier `/output/result.json` wording is superseded at the exact-path
level by the accepted worker-control contract. `/output/output.json` is the
reserved protocol completion manifest and declared outputs are directory
trees; a second top-level result document would be unmeasured auxiliary
material. This milestone declares one `proposal` output at
`/output/proposal/` containing:

- `result.json`: bounded application metadata (task identity, disposition,
  changed paths, summary and claimed verification), never a protocol identity
  substitute;
- `candidate/`: the complete modified copy of the staged source subset;
- `change.patch`: a review convenience derived inside the worker, not the
  custody identity; and
- `verification.txt`: bounded stdout/stderr and exit status from the focused
  command, with no credential or provider diagnostic content.

The worker publishes `/output/output.json` last. That canonical document
binds the assignment and measured `proposal` content manifest. Manager custody
collects and seals the declared tree; the operator trusts neither
`result.json` nor `change.patch` in place of independently diffing the
candidate tree against the recorded input manifest and rerunning verification
outside the worker.

## Recommended patch boundary

The implementation is one bounded vertical slice with four explicit owners:

1. A dogfood-only Python operator module under `v12/python/tools/` composes the
   public W6636 operations, source staging, explicit credential delivery,
   evidence transcript and every cleanup ending. Its unit tests use injected
   engine/transport/provider capabilities and golden documents/vectors.
2. A narrow Docker worker-entry transport under the Python Worker Manager
   adapter boundary sends correlated `describe`, `consider` and `work` frames
   to the exact started container and returns bounded stdout/stderr/status.
   It has no scheduling, source, Git or provider policy. Transport loss is not
   clean completion and does not manufacture an agent answer.
3. A dogfood Claude image/entrypoint under the worker or dogfood tool surface
   reuses `baton_worker.py`, injects a Claude agent, copies `/input/source` to
   private `/tmp` space, runs the frozen task there, verifies it, and writes
   only the declared proposal tree. Provider argv is closed and golden-tested;
   no provider text can become protocol framing or success identity.
4. The first-task fixture is a frozen task document plus the minimal staged
   ping-pong files needed to add and run the coverage. The retained transcript
   records input/tree/image/task/assignment/runtime/output digests, independent
   verification and the operator disposition, while redacting credentials
   and bounded provider diagnostics.

The implementer must revalidate exact module names against the then-current
tree and avoid the existing unrelated modifications in Python authority,
custody and workspace files. A reusable entry point is required; a test-only
fixture or shell transcript is not the milestone.

## Required regression matrix

- **Positive:** one real Claude container receives the frozen task and
  read-only source, produces the declared proposal, publishes a correlated
  completion, is collected/sealed, is independently diffed and passes the
  focused command outside the worker.
- **Provider negative:** missing explicit credential, provider nonzero exit,
  malformed/bounded provider response, or no candidate never becomes
  `completed` and still takes the proven runtime/credential cleanup path.
- **Control negative:** wrong session/assignment/generation, malformed frame,
  missing completion manifest, undeclared output and output outside
  `/output/proposal` refuse through existing typed boundaries.
- **Transport:** EOF, timeout or Docker attach/exec failure records uncertain
  or failed execution as appropriate; none implies the container is absent.
- **Retry:** an exact operation replay does not start a second container,
  dispatch a second agent turn or replace an existing proposal. A fresh
  attempt gets fresh input, launch, credential and output roots.
- **Isolation:** the source input and canonical checkout remain byte-for-byte
  unchanged, the worker has no authority store/runtime socket, and the only
  writable host bind is its assignment workspace.
- **Cleanup:** success and every post-start failure destroy the exact runtime,
  positively observe absence, tear down the attempt credential, and preserve
  an unresolved attempt rather than claiming cleanup when that proof fails.

## Checkpoint decomposition — confirmed 2026-08-29

W38956 is the acceptance roll-up, not one giant implementation assignment.
The implementation handoff at sequence 39022 and the recommended patch and
regression boundaries above remain valuable revalidation, but are superseded
where they imply delivering every seam under this one claim.

Use four short, independently claimed and reviewed critical-path checkpoints:

1. prove the reusable Docker worker-entry control transport;
2. inject and prove one real Claude adapter/image against that transport;
3. compose the minimum supervised operator path across declared input,
   explicit credentials, launch and correlated output; then
4. run and independently verify the frozen first useful repository task.

Checkpoint 3 depends on 1 and 2; checkpoint 4 depends on 3. Checkpoints 1 and
2 may proceed independently only after their shared worker-control contract
and file ownership are explicit. Record the broader negative, retry, cleanup
and defensive matrix as a fifth, non-gating hardening lane; it blocks the
first useful result only when an observed defect can make that result false.

Each checkpoint owns a child dossier and Work, one claim, one bounded result
and independent review. W38956 closes only as the roll-up after the four
critical checkpoints prove its acceptance boundary.

The active W38956 implementer may finish and record only the temporary
transport probe and dossier revalidation already in flight when this ruling
landed. It must not begin the bundled repository implementation. It returns
the parent claim so decomposition can occur without changing implementation
scope underneath an active episode.

## Active-episode non-preemption clarification — confirmed 2026-08-29

The final paragraph above is superseded for the already-running assignment
episode. By the time its stop instruction was published, the cooperative v11
ACP turn had progressed into repository implementation and Baton had no safe
in-turn preemption mechanism. Do not terminate the turn merely to simulate
control v11 does not possess, and do not discard or revert its changes.

Let this one W38956 implementation episode finish naturally. Its handoff must
name every changed file, completed seam, incomplete seam, test result and
remaining concern. The reviewer then maps that evidence into the checkpoint
Jobs: a coherent completed result may satisfy or seed a child, but is not
silently treated as reviewed completion. All remaining work is decomposed
before any later implementation claim on this campaign. This one-episode
exception does not revive the superseded giant-Job model.

## Acceptance

- A single documented command starts the trial from a clean operator-owned
  state and records the exact input, task and provider.
- A real Claude Docker worker produces a useful candidate change under
  `/output` and exits cleanly.
- The returned result is correlated to the one assignment, collected and
  sealed by the manager, and independently inspected and tested by the
  operator or reviewer.
- The canonical checkout, Baton authority and unrelated host paths remain
  unchanged by the worker.
- A durable transcript names the input identity, assignment, container,
  output identity, candidate artifact, verification and final disposition.

Success declares v12 ready for bounded supervised dogfooding, not production
cutover. The next useful task should be able to reuse the same entry point
without reconstructing a test harness by hand.

## Implementation revalidation — 2026-08-29 (`baton.claude`, W38956 impl claim)

The recorded plan above was revalidated against the working tree before any
code was written. Items 1 and 2 hold exactly as written. Three facts the
earlier revalidation did not reach were found, and each one decides something
the implementation cannot proceed without.

### Confirmed: the accepted start vector cannot carry a worker-entry
### conversation, and `docker attach` cannot repair it

`oci.run_vector` composes `docker run --detach` with no `--interactive`, so a
started container's stdin is `/dev/null`. The reference worker reads EOF
immediately and exits 0 — which is exactly what
`test_the_adapter_starts_a_worker_that_actually_runs` asserts and is the right
assertion for a container nobody is going to speak to.

A worker-entry conversation needs the opposite: a stdin that stays open, frames
written to it, its answers read back, and finally an EOF, because `serve`
returns 0 only on a clean end of input. A session ended by a signal is not a
worker that finished, and a manager that stopped the runtime to end the
conversation would be manufacturing a clean ending out of a kill.

Three candidate transports were MEASURED against the development host's daemon
rather than argued about; the script and its recorded answers are
`evidence/w38956-transport-probe.py` and
`evidence/w38956-transport-probe.txt`.

| transport | frames in/out | stderr apart | EOF propagated |
|---|---|---|---|
| `run --detach --interactive` + `docker attach` | yes | yes | **no** |
| `run --detach --interactive` + `docker exec --interactive` | yes | yes | yes, status 0 |
| `docker create` + `docker start --attach --interactive` | yes | yes | yes, status 0 |

`docker attach` is therefore **not usable**, and this is the measurement rather
than a preference: with `-d -i` the daemon holds the container's stdin, so the
attaching client closing its own stdin does not close the worker's. The probe
records the container still running after the transport gave up. A design that
had assumed otherwise would have discovered it against a real Claude container.

**Decision (pinned): the transport is `docker exec --interactive` against the
exact started runtime id.** The rejected alternative is recorded with it,
because it is the more obvious one:

- `docker create` + `docker start --attach --interactive` keeps one container
  and one entrypoint invocation, and it BLOCKS for the whole session. The
  accepted arc journals `runtime.start` and returns, and then reconciles,
  freezes, takes intake and destroys. Making the start blocking inverts that
  ordering, and re-attaching to an already-exited container instead would make
  a runtime go `exited -> running -> exited`, which the accepted absence and
  reconciliation model does not describe.
- `docker exec` leaves the container lifecycle monotonic — created, running,
  stopped — which is the one the accepted operations already model, and puts
  the blocking where blocking belongs: inside the transport operation.

Its cost is stated rather than hidden. The start vector gains `--interactive`,
so PID 1 is a worker instance that blocks on a stdin nothing writes to; the
conversation is a second invocation of the same program under `exec`. The
idle PID 1 reads nothing, writes nothing, holds no capability the container
does not already have, and is what keeps the runtime alive to be spoken to.
A container whose launch document is unreadable still exits non-zero at PID 1
and is never exec-able, which is the property that matters preserved.

`--interactive` is **opt-in at adapter construction and defaults off**, so
every accepted regression over the detached reference worker keeps its exact
meaning. A start that composes it and is never spoken to would hang rather than
exit, which is a real difference, so it is never composed by default.

The exec session's identity was measured too, because it decides whether the
worker can write at all: `docker exec` INHERITS the container's `--group-add`,
answering `uid=65532 gid=65532 groups=65532,<workspace gid>` and writing the
bound `/output`. So the transport needs no `--user` override, and W33936's
ruling that the pinned `65532:65532` identity is untouched holds unchanged
through the exec.

### Confirmed: `--network none` is unconditional, and a real provider needs egress

`oci.RESTRICTIONS` applies `--network none` to every runtime, unconditionally,
and every accepted case in this campaign asserts it. W17110 ran a real Claude
CLI with network, but through the spike's OWN Docker lifecycle — never through
this adapter — so nothing in the accepted manager path has ever started a
container that could reach a provider.

**This is a blocker of the kind this finding says stays in W38956**: with the
restriction as written, the milestone's own positive case cannot happen, and a
run that reported success without egress would be reporting something other
than a real Claude worker.

**Decision (pinned, and it needs approver confirmation before the first live
trial): the network posture becomes an explicit, deployment-supplied adapter
operand whose only default is `none`.** Specifically:

- `--network none` stops being a constant of `RESTRICTIONS` and becomes the
  DEFAULT value of one named operand. An adapter constructed without naming a
  posture composes exactly the argv it composes today, so no accepted case
  changes meaning and no existing deployment silently gains egress.
- Naming any other posture is refused unless the caller supplies it
  explicitly, and the composed value is recorded in the attempt's evidence
  transcript beside the credential and the image.
- The operand is a bounded engine network NAME. It is not an escape hatch for
  arbitrary engine flags, and the adapter gains no other network vocabulary.

What this deliberately does NOT do: it does not decide that unrestricted
bridge egress is an acceptable long-term posture for an untrusted agent
container. It makes the grant explicit, named at one operand, defaulted closed
and recorded — and leaves the narrower question (an egress allowlist or proxy
for provider traffic only) as work this milestone does not own. The operator
authorizes the exact posture at trial time, in the same act that authorizes the
exact credential operand, and the two are the only grants that command takes.

### Confirmed: the v12 authority session does not carry the whole port surface

`AuthorityPort` requires seven session operations, and
`baton_v12.authority.session.Session` — the only object `Authority.session`
mints — implements six of them. `publish_answer` is not a v12 authority
transition and could not be: it publishes a model answer into **Baton**, which
is a different system, and the port's own docstring says the deployment is what
holds both.

This is not a defect and no Baton finding is owed for it. It is the injection
boundary working as written: the port names what the manager USES, and trusted
deployment composes the object that carries it.

**Decision (pinned): the dogfood command composes the port's session itself** —
the six real operations delegate to the minted `Session`, and `publish_answer`
refuses with a typed refusal naming this pilot's boundary. This milestone runs
no `inquire`, so the member is never reached; a facade that quietly answered
one would be inventing a Baton publication nobody performed.

### Confirmed: cooperative output is required and is not custody

`DEPLOYMENT.md` states, and W36540 owns, that unconditional manager custody of
worker-selected modes does not exist yet: a worker writing mode `0600` leaves
material the manager fails closed on. This finding's exclusions already accept
that boundary for this bounded pilot. The consequence for the implementation is
concrete rather than philosophical: the dogfood worker writes its proposal
tree group-readable, deliberately and as a stated cooperation, and a failure to
collect or clean up is preserved as an unresolved attempt rather than reported
as success.

## Checkpoint graph materialized — 2026-08-29 (`baton.codex`)

The one-episode exception returned at Baton sequence 39342. Its implementation
is mapped into four independently accountable child Jobs rather than continued
under this parent:

1. W39356 — `findings/finding-docker-worker-entry-transport/` owns independent
   review and completion of the delivered Docker control transport.
2. W39357 — `findings/finding-real-claude-adapter-image/` owns the real Claude
   provider adapter and pinned worker image.
3. W39358 — `findings/finding-minimal-supervised-operator/` owns the smallest
   reusable supervised operator composition. It is blocked on W39356 and
   W39357.
4. W39364 — `findings/finding-first-useful-task-acceptance/` owns the frozen
   first task, retained transcript and independent accept/reject result. It is
   blocked on W39358.

The parent is gated on W39364 so the roll-up stays dormant until the final
critical-path result returns. The broader defensive matrix is W39366 at
`work/records/2026/08/finding-v12-supervised-dogfood-hardening/`. It is a
separate top-level, low-priority parked Work with no containment or dependency
edge into W38956. That makes it genuinely non-gating: it returns to the
critical path only if observed evidence shows a defect that can make the
positive dogfood result falsely succeed.

File ownership is disjoint at offer time. W39356 owns the Python manager
transport, OCI vector additions and their focused tests. W39357 owns new
worker-side Claude adapter/image files and their tests. W39358 owns the new
operator module, operator documentation and composition tests. W39364 owns its
child evidence and the external candidate/acceptance transcript; it never
edits the canonical ping-pong source as part of the trial. Shared-file changes
require a recorded handoff before editing.

## 2026-08-30 — boundary-inventory hardening leaves the dogfood path

**Supersession:** W39666 remains the durable owner of the worker-entry
transport's three receiving-boundary inventory entries, but it no longer gates
W39356 or the first useful dogfood task. The transport's actual validation,
closed endings, focused regressions and real-Docker conversation are present;
the shared inventory registration is a cross-cutting hardening/accounting
check whose completion currently waits on the separate custody program.

Keeping W39356 behind W39666 indirectly placed the complete W43974 → W43975 →
W43977 custody-hardening chain ahead of W39358 and W39364. That contradicts
this campaign's approved top-down vertical-slice rule. Remove only that
dependency edge. W39666 stays open and attributable, and any observed defect
that can make the positive dogfood result falsely succeed still returns to the
critical path; unimplemented inventory bookkeeping alone does not.

## 2026-08-31 — first live attempt rejected; critical path continues

W39364 closed `non-satisfying` after the one authorized live provider attempt.
The supervised platform arc resolved, but the worker answered `unable`, the
candidate was byte-identical to the four-file input, and hard-coded discard
removed it before direct reviewer inspection. The explicit rejection is
`findings/finding-first-useful-task-acceptance/review-2026-08-31T04-56-33Z.md`.

The continuing critical path is explicit rather than hidden in the closed
attempt:

- W51473 fixes the operator's retention decision and terminal-retained
  resolution; it blocks this parent.
- W51487 owns a later fresh useful-task attempt after W51473 and after new
  operator authorization; it also blocks this parent.
- W51476 owns the separately observed human-contract preflight interval. It is
  real but does not independently authorize or force another live attempt.

No W39364 credential/network grant carries into W51487, and no second provider
turn is authorized by this record.
