# Finding: make live worker progress observable

**Status:** confirmed v12 usability follow-up; independently scheduled

**Binding:** `baton:work/records/2026/09/finding-live-worker-log-observability`

**Canonical Baton Work:** `W61599`

**Roadmap:** `work/records/2026/08/finding-v12-isolated-agent-workers/`

**Foundation:**
`work/records/2026/08/finding-v12-worker-custody-provider/`, W43972

## Observed — 2026-09-01

During the W52821 live v12 dogfood attempts, the worker could remain active for
minutes while its container stdout was empty. `claude --print` did not expose a
useful incremental stream there, but Claude's native session JSONL inside the
container did show ongoing messages and tool activity. Merely formatting those
records as JSON, without an agent-specific semantic filter, produced a useful
operator view with readable indentation and color-coded keys and values.

An operator should not have to infer progress from CPU, network traffic, or a
container process list. UX suffers when people cannot tell whether a worker is
starting, thinking, using tools, testing, waiting, failing, or making no
progress.

## Confirmed MVP boundary — 2026-09-01

Every v12 attempt must make its available native agent/session log continuously
observable through the manager-owned `result/logs/` boundary already ruled by
W43972. This is a follow-up to that closed Work, not a reopening of its result
envelope decision.

The first useful implementation deliberately avoids inventing a normalized
agent-event vocabulary. The manager captures the provider's native JSONL (and
plain stdout/stderr when that is all a runtime offers) from attempt start,
retains it on success and failure, and publishes a stable attempt-relative log
locator. A viewer follows appended records and, for JSON objects, presents
jq-style pretty-printed output with indentation and syntax coloring. Non-JSON
lines remain visible as text rather than being discarded.

The v12 TUI must be able to follow this live view from the selected attempt so
an operator can quickly answer "is this working?" without entering the
container or discovering provider-private paths. A CLI tail/follow surface is
an acceptable earlier vertical slice and gives the TUI one manager-owned
source rather than direct Docker access.

Native logs may contain prompts, source excerpts, tool output, or
provider-exposed reasoning metadata. The unfiltered view is therefore an
operator/reviewer surface with the same access boundary as the attempt, not a
public team feed. Credential values must never be deliberately copied into the
log, but a new redaction or normalized-clean-stream design does not gate the
MVP. A later hardening Work may add a sanitized compact event stream, bounded
retention, searching, filtering, and richer provider-specific presentation
after live use demonstrates what is valuable.

The worker's stdout is a useful fallback and diagnostic surface, but it is not
the authoritative log location. Manager-owned files survive worker exit and
remain correlated to the attempt. Clean completion seals them with the result;
forced or abnormal termination preserves the partial logs and marks them
incomplete rather than silently losing the evidence.

## Acceptance boundary

- A live attempt publishes one stable manager-owned log locator under
  `result/logs/` without requiring container inspection.
- Native JSONL is copied incrementally and can be followed before the worker
  exits; plain-text runtimes remain observable.
- The CLI can follow the live stream and pretty-print JSON records without
  buffering until completion.
- The v12 TUI can render the same stream with jq-style indentation and syntax
  coloring from an attempt detail surface.
- Success, provider failure, forced termination, and manager restart preserve
  correlated complete or explicitly incomplete logs.
- Tests prove incremental visibility rather than only inspecting a completed
  file.
- Normalized/sanitized event semantics, redaction hardening, search, and log
  retention policy are recorded follow-ups and do not block the vertical
  slice.

## Reviewer revalidation — 2026-09-01 (`baton.codex`, W61599)

### Observed — the current transport has no durable live-log seam

The current worker set is the deterministic `ScriptedAgent` and the dogfood
`ClaudeAgent`. The scripted agent emits no native session events. The Claude
adapter invokes `claude --print --output-format json`; `_ran_provider` drains
that provider stdout into one bounded terminal record, derives at most the
closed `api-error|unclassified` failure word, and discards the record. Provider
stderr and both streams of provider-edited verification code stay on
`subprocess.DEVNULL`. Claude's private home is under the container's `/tmp`, so
the native JSONL observed during W52821 is deliberately not a manager locator
and disappears with the runtime.

`baton_worker.py` reserves stdout exclusively for the length-prefixed
`baton.worker-entry/1` request/reply channel. It gives an injected agent only
`consider` and `work`; there is no event/log sink. On the manager side,
`worker_entry.converse` rejects surplus stdout as transport loss. The dogfood
deployment's `_Channel` does drain the exec process's stderr concurrently, but
it retains only a bounded terminal window for `finish()` and discards the
rest. No current manager component appends either stream to durable storage.

This leaves two viable transport families to rule before implementation:

1. let a provider adapter turn its provider-private event source into a
   worker-owned log stream (stderr is the existing unframed stream), while a
   deployment-supplied channel appends that stream to a manager-owned file; or
2. version the worker-entry contract with interleaved, correlated event frames
   and teach both peers to distinguish them from replies.

The first is the bounded vertical slice: provider-private paths remain inside
the adapter, plain stderr is a natural fallback, and stdout framing does not
change. The second is appropriate only when typed provider-neutral event
semantics are actually being introduced; doing it merely to transport raw
lines would make the deferred normalized vocabulary gate the first viewer.

### Observed — the ruled `result/logs/` shape is not a current capability

`workspaces.assignment_workspace` creates
`workspace/result-<attempt-id>` before launch, but returns only the `inputs`
and `workspace` roots. It grants the whole workspace and the result directory
to the worker's writable group. The dogfood OCI adapter then mounts that whole
workspace at `/output`. Separately, `OciAdapter._custody()` derives the
unmounted manager-owned `custody/<attempt-id>` directory where sealing copies
accepted outputs. No allocator or adapter currently creates a `logs/` child,
returns a nominal result/log capability, or publishes an attempt-relative log
locator.

A raw pathname assembled by the dogfood deployment would repeat the custody
defects that nominal allocation corrected. The capture implementation needs a
manager-minted log sink/locator derived from the exact allocated attempt. The
worker must not receive filesystem write authority over the manager-owned log
file: group write on an ancestor permits rename or unlink even if the file
itself is read-only. A manager-opened sink receiving stream bytes preserves
the W43972 rule that the worker can emit history but cannot rewrite it.

The sink must exist and be marked incomplete before the exec session starts.
Only a positively observed clean stream ending may mark it complete. A manager
restart can then preserve a truthful partial file without pretending it can
reattach to an exec pipe that the prior process owned. Continuing capture
across restart is a later strengthening unless the runtime/engine supplies a
replayable source; preservation and explicit incompleteness are the current
acceptance requirement.

### Confirmed conflict — raw native logs are credential-capable bytes

The unfiltered-log ruling cannot yet be implemented consistently with the
security decisions it cites as foundation:

- W43972 requires credential material in `result/logs/` to be excluded or
  redacted.
- The roadmap's host-credential ruling keeps bearer bytes absent from logs and
  output artifacts.
- W39357 proved that the Claude process and provider-edited verification code
  can read the attempt credential. Its accepted correction therefore sends
  their streams to `DEVNULL`; printing the bearer was sufficient to leak it,
  and an adapter-local redactor was rejected because that adapter must not read
  the bearer.
- Section 13's live-secret walk detects exact registered values in structured
  durable documents. It is not a streaming redactor. More importantly, the
  delivered Claude credential is opaque provider text: a tool can print one
  token or transformed subset from that document, which cannot be recognized
  by comparing against the whole registered value without parsing a provider
  credential that the manager contract intentionally treats as opaque.

A native session transcript includes tool input/output and can therefore carry
exactly the bytes W39357 withheld. Calling the surface restricted changes who
may read a leak; it does not make the credential absent from a durable log.
Likewise, saying Baton does not *deliberately* copy a credential does not hold
the stronger existing rule when Baton deliberately copies an untrusted stream
whose producer can read it.

**Open decision — implementation gate:** the approver must choose and record
one of these mutually exclusive boundaries before implementation begins:

1. preserve W43972, W39357 and section 13, and narrow this first slice to
   manager-authored lifecycle/progress facts or another closed provider-safe
   event surface; raw prompts, tool input/output and native transcripts wait
   for credential isolation or an enforceable sanitization boundary; or
2. explicitly supersede the credential-free-log decisions for one restricted
   secret-capable diagnostic surface, and define its access, retention,
   teardown and incident consequences now rather than deferring them as
   hardening.

The first option is recommended. It still permits the capture/locator/CLI
plumbing to be proved with the scripted worker and credential-free fixtures,
then widened only when a provider adapter can make a stronger claim than
"these are the bytes the credential-capable child wrote." The current text's
simultaneous promises of unfiltered native logs, no gating redaction, and
credential-free durable surfaces cannot all be true.

### Proposed implementation boundary after the ruling

If the security-preserving option is accepted, implement in this order:

1. extend allocation with one nominal attempt-result/log capability and create
   the manager-owned log sink plus stable relative locator before runtime
   start; never accept a caller-supplied log path;
2. let the deployment's `_Channel` append the unframed worker stderr stream as
   it drains it, with an incomplete marker established first and a complete
   marker written only after clean EOF/exit; preserve text lines and bounded
   JSON records without waiting for process completion;
3. add an injected worker-side log emitter. `ScriptedAgent` supplies safe
   incremental fixtures; Claude initially emits only the closed progress facts
   authorized by the approver's ruling, not its raw credential-capable session
   document;
4. expose the manager-derived locator/read/follow operation. A viewer reads
   through that operation rather than accepting an absolute path or entering a
   container; JSON presentation is a client concern and non-JSON lines remain
   verbatim;
5. prove first-byte-before-exit, bounded long/non-JSON input, success, provider
   failure, forced termination, manager restart with explicit incompleteness,
   symlink/rename attempts, cross-attempt access refusal, and absence of any
   Docker/container-inspection dependency.

There is no v12 TUI implementation in the current tree. Its item remains
ordered after the CLI source and after the separately ruled first read-only
viewer exists; W61599 should not create a command-capable TUI or a second log
reader contract.

## Approver ruling — 2026-09-01

**Supersession:** The earlier confirmed MVP text that authorized incremental
capture and retention of unfiltered native JSONL or arbitrary stdout/stderr is
superseded. Pretty presentation does not change the credential-capable byte
class of a native transcript. W43972, W39357 and section 13 remain in force:
durable `result/logs/` content is credential-free.

The first slice instead emits and retains a closed provider-safe progress
stream. Its records may identify the attempt/session correlation, lifecycle
phase, heartbeat, bounded tool category or name, test start/end and status,
completion/failure class, and observation time. They carry no prompt text,
reasoning text, source excerpts, tool arguments/results, command bodies,
provider stderr/stdout, credential values, or arbitrary provider prose.
Unknown information stays unknown rather than being filled with native text.

The manager creates and owns the sink before runtime start, appends records as
they arrive, and publishes one stable relative locator. The CLI follows that
stream without buffering until completion and pretty-prints JSON records;
non-JSON input is valid only for a driver whose closed safe surface is defined
as bounded plain text, never as an escape hatch for arbitrary child output.
The later read-only TUI follows the same manager operation.

An explicitly authorized operator may still inspect a live container's private
native transcript for diagnosis. That transcript is not a Baton result
artifact, is not copied into `result/logs/`, and disappears with the runtime.
Durable raw transcripts remain deferred until a separately approved credential
isolation or enforceable sanitization boundary exists. This preserves the UX
goal—operators can tell whether a worker is progressing—without weakening the
credential contract.

### Confirmed default liveness projection

Most wedge diagnosis needs no log content at all. The adapter/manager therefore
publishes a monotonic count of native session bytes it has observed and the
manager's receipt time for the latest observed activity. The Jobs/attempt
summary can render, for example, `Log 1.40 MiB · updated 4s ago`; a changing
count and recent update are enough to show that the provider is still moving.
The manager clock is authoritative for age. No provider timestamp, native log
path, or content enters this projection.

The counter is an observation, not proof of useful progress: repeated noise can
grow it, a quiet model call can leave it unchanged, and a provider may expose
no measurable session stream. It never renews a claim, clears a gate, extends a
deadline, or authorizes recovery. A stale count is a cue to inspect or probe,
not an automatic kill decision. The provider-safe progress stream remains the
drill-down surface when the summary is insufficient.


## Implementation decisions — 2026-09-01 (`baton.claude`, W61599 first slice)

**Confirmed by implementation. Nothing here supersedes anything.** These are
the three questions M61707's ruling left open that the code had to answer, and
they are recorded because each one is a decision a later reader would otherwise
have to reverse-engineer from a conditional.

### The projection lives in the control store, as two nullable attempt columns

Schema 14 adds `activity_bytes` and `activity_at` to `attempts`, under a
both-or-neither CHECK. The reasoning:

- the ruling says the JOBS/ATTEMPT SUMMARY renders it, and a summary is a
  projection of this manager's durable per-attempt record;
- the reader is a DIFFERENT PROCESS from the manager running the attempt, so an
  in-memory counter could not answer it at all; and
- putting it in the store keeps the default view free of any log locator. An
  operator asks "is this moving?" without needing to know that a sink exists,
  which is what makes the projection the DEFAULT rather than a drill-down.

A count with no instant is an unreadable age and an instant with no count is
freshness about nothing, so the table keeps them together rather than trusting
a writer to.

### A repeated total is accepted and does NOT move the instant

An observer polling a stream that has produced nothing is behaving correctly,
so its report is not a refusal. But the instant is the age of the latest
observed ACTIVITY, and advancing it on a repeat would make a wedged worker read
as freshly alive to the one operator relying on this to notice. A decrease
refuses outright: a stale or confused observer must not be able to make a
progressing worker look stalled.

This is the projection's whole value. A liveness display that can lie is worse
than none, because an operator who trusts it stops looking.

### A failure to publish is dropped, never raised

The dogfood channel's stderr drain exists so a full pipe cannot block the
container and hang the session. Publishing happens on that thread, so a busy
store, a refused observation or an observer fault is swallowed there: a
diagnostic projection that could raise out of the drain would wedge the very
session it was added to observe. An operator who misses a publication is
exactly as informed as one running the previous build.

The cadence — at most one publication a second, and always one at end of
stream — is the drain loop's own resource decision. It is the resolution of an
operator reading "updated 4s ago", not of the stream.

### What this slice deliberately did NOT build

The manager-minted `result/logs/` capability, the sink, its incomplete/complete
marking, the closed provider-safe progress stream and the CLI follow view are
all still ahead. This slice needed none of them, which is why it went first:
what crosses from the observing loop is a LENGTH, so M61707's credential-free
durable surface holds by construction rather than by a redaction boundary that
does not exist yet.

## 2026-09-14 — selected minimum v12 activity subset, W165782 claim167877

Owner W2 ruling09:04:44Z/reroute167871 selects the minimum release subset here:
positive provider-safe native-session growth and manager-owned last-activity
instant, without raw transcript content. Correct the existing outer-stderr
misclassification, synchronous publisher backpressure and zero-byte EOF stamp.
Use bounded/coalescing publication so mandatory drain cannot block. Preserve
absence/partial state honestly across restart; do not invent reattachment.

This supersedes treating all PLAN items5–9 as minimum v12 release gates. Native
stream follow, safe-progress log sink expansion, coloring, pause, search/filter,
retention policy and rich telemetry remain deferred v13 scope here; no raw
transcript authorization. Current source dogfood_operator._activity_observer
still publishes counts from _Channel outer stderr; no supersession established.
The existing Work owns this correction, not new viewer W167896. The viewer
consumes trusted activity or displays unknown and edits only its three new files.

Before changing shared source, revalidate the supported stage/provider producer
and retain focused actual-boundary fixtures (fake provider, no live model).
Acceptance is positive growth before completion, no unrelated-stderr/EOF false
activity, no blocked-publisher drain deadlock, and restart preserving unknown/
partial facts. Necessary tests within this subset are authorized by standing
policy. No generic telemetry, model run, engine test or cumulative-time gate.
W165782 only pins scope and requests scheduling; this entry is not a claim or
implementation by the reviewer. Rich remainder is preserved, never waived.

### Minimum-outcome gate clarification

For release ordering, current W61599 completion is the independently accepted
minimum activity correction above. Earlier follow/color/search/retention/native
stream expansion remains historical deferred design material for W39649/v13
scope selection, not a condition of this minimum Work outcome. This supersedes
the earlier PLAN assumption that every rich-stream item must finish before
W61599 can close. Closing the narrowed outcome must explicitly name the deferred
items and does not assert their implementation. No v13 execution is authorized.

## 2026-09-15 — owner selects concrete activity design after W63255 handoff

Slawomir agreed to prioritize Claude implementation of W63255, followed by concrete W61599 activity-source and safe-transport design. This supersedes pending scheduling for design only, not the minimum product outcome or rich-UX deferrals. After passing W63255 for independent review, the configured baton.impl Handler may unpark and claim W61599 for this design-only turn. Do not interrupt another active claim.

Read the complete existing review-2026-09-01T14-24-19Z.md, current FINDING/PLAN and corrected advisory baton:work/records/2026/09/finding-v12-live-progress-prework/PREWORK.md SHA256 65243e410ae3526b1895c7f53bfae9453b8b8e933db04953889fdd27ce5778c9. Produce one concrete design here identifying the supported incremental provider activity source, a closed count-only worker/deployment transport, bounded/coalescing nonblocking publication and positive-growth-only manager freshness. Compare actual source/test bodies and retained evidence before naming a gap. Provider stdout being final JSON is not evidence of incremental native progress. Identify the exact content-free observation operation, lifecycle/teardown ownership, proposed source/test paths and deterministic production-boundary validation.

Design owns only this dossier's new design document and FINDING/PLAN updates; no product/test/main-documentation edits, tests/probes, live models/engines or protocol implementation. If a producer fact cannot be established from source and retained evidence, specify the exact unresolved question and smallest proposed validation instead of inventing it. Caller-versus-owner placement and scoped test changes need no new owner gate. No generic telemetry, rich stream UX or extra acceptance campaign is selected. Return the concrete recommendation to baton.ops for reviewable scope selection before implementation. Do not claim W61599 complete from this design.

## 2026-09-15T03:16:10Z — independent design review, claim174457

**Confirmed:** reviewed the submitted ACTIVITY-SOURCE-DESIGN-174354.md SHA256
696c117d71bc9740d33e458bb93a2e8e6a82dd424c02d55938539f53d65ac3f7 against
current source and retained evidence. `review-2026-09-15T03-16-10Z.md` requests
changes before implementation selection. No product/test changes or execution.

The design's assertion that no native incremental observation exists is
superseded by this clarification: this FINDING already retains the W52821
operator observation of private native JSONL growth. Exact current invocation
file identity remains open. A fake provider timing experiment cannot select
the real CLI source, and multiple reads can all belong to its final JSON.

**Confirmed:** state/1 has a closed text-valued member contract; the proposed
integer addition needs a typed/versioned design. Ordinary exchange consumption
is in single_worker, omitted from the proposed path set. **Inferred:** the
proposed independent periodic state writer can overwrite answered/faulted
after terminal publication, causing the existing causal validator to discard
the terminal; separating threads alone does not establish bounded teardown.

**Proposed, not implementation authority:** revise around private native-file
metadata, one separately versioned optional count-only exchange document with
exact operation binding, and bounded/coalescing publishers owned by the worker
and the actual serving composition. Preserve lifecycle documents, unknown/last
observed state and receipt-time semantics. The review names path ownership,
compatibility, source-baseline and finalization cases required in that revision.
Return baton.ops for selection; W61599 remains unfinished and blocks W2.
The 2026-09-14 minimum selection and W39649/v13 rich-UX deferrals are unchanged.

## 2026-09-15 — owner selects the bounded design revision (M174518)

Slawomir selected the bounded design revision recommended by
`review-2026-09-15T03-16-10Z.md`
(SHA-256 `534d4b37aaff995d94703eb11c8e15bdf479a2ec14a50fa55edbda5d121576d8`),
to follow the W63255 implementation handoff (returned at seq 174481).

Selected for revision: **native-file identity**, a **separate optional
count-only activity transport**, **compatibility and exact binding**,
**ordinary serving ingestion**, and **bounded publication and cleanup**.
Lifecycle documents are preserved unchanged, and the minimum/v13 boundary
stands. Design only — no product edits, tests or live execution — returning to
`baton.ops` with the concrete revised design and path ownership for
implementation selection. `ACTIVITY-SOURCE-DESIGN-174354.md` is superseded by
the revision recorded beside it; it remains as history.

## 2026-09-15 — owner completes the activity-document selection (M174565)

Slawomir selects the separate optional `activity.json`, **written to a temporary
file then atomically renamed over the published file — never renaming the
published file away first**. One publisher, a bounded latest-count slot, and
exact **attempt / operation / sequence / command** binding. Missing activity
preserves **unknown or last-observed** state.

The design must be completed with concrete nonblocking manager ingestion,
bounded publisher lifetime and cleanup **even when publication stalls**, exact
document and count limits, accurate old-reader compatibility, and
**current-invocation native-session file identification derived from source and
retained evidence**. Lifecycle documents and the minimum/v13 boundary are
preserved. Design only. The completed packet returns to `baton.feat` for focused
independent review, then `baton.ops`.

## 2026-09-15T03:30:15Z — review174592: selected document stands; design incomplete

Reviewed ACTIVITY-DOCUMENT-DESIGN-174572.md SHA256
cdf220ab2d5cffa5604fab56ae022b688b1ab44d54065f53f60cc7e745ed37eb;
`review-2026-09-15T03-30-15Z.md` requests completion before implementation
selection. Optional activity.json, atomic replacement, separate typed parser,
unchanged lifecycle documents and minimum/v13 boundary remain selected.

**Confirmed:** manager.sweep executes serial passes, so synchronous diagnostic
file/store work can delay following stages and cleanup; calling it a step does
not supply nonblocking ingestion. Identity equality does not expire a completed
operation, stop a thread or prove cleanup. **Inferred counterexample:** two
operation publishers can overlap after one is abandoned and collide on the same
temporary file. An exact publisher lifetime/exclusion and late-write policy is
still required; the selected file pattern is not being reopened.

**Explicit correction of the174572 source deduction:** production _scratch
does not cache its new directory in _home; _home is assigned by the constructor's
test injection only. Describe invokes no Claude provider. A reused _prepared_home
is not proved empty. Fresh invocation HOME is useful provenance, not proof that
all matching files are native sessions. The proposed count formula can regress
when a file shrinks while remaining above its initial baseline; track last size
and freeze further observations on ambiguity. Bind per-operation observation to
the attempt-wide cumulative owner coherently. These are corrections to design
claims, not executed product failures.

Old-reader compatibility is statically known: MAX_EVENT_ENTRIES=64; extra names
are reported as foreign without being read, and exceeding the cap invalidates
the observation. Pin bounded staging/leftover headroom in the revised design.
Return baton.ops with the concrete corrections and retain W61599/W2 gates.
No product/test changes or tests/probes/live execution; verification execution0s.

## 2026-09-15T03:50:47Z — review174739: concrete remaining design boundaries

Owner174641 requested completion; reviewed author174658/174656 packet
ACTIVITY-DOCUMENT-DESIGN-174645.md SHA256
25bc279ca43637f1e74427ce6847b1ffe97f450b35254b6e849e6204b5a63d46.
Review `review-2026-09-15T03-50-47Z.md` accepts the corrected scratch deduction,
work-only baseline and monotonic/freeze counting direction, publication cadence,
no-replacement direction and64-entry headroom. These supersede those outstanding
parts of review03:30:15Z; optional activity.json and atomic replacement stay
selected. No product implementation is accepted.

**Confirmed:** observe_activity has no live-state/publication-generation guard.
**Inferred counterexample:** a greater-total write paused after a nonterminal
check can resume after terminal/close, advancing receipt time for the same
operation. Binding/repeat/regression checks do not reject it. Finish explicit
delayed-final-count semantics or an actual revocation boundary before claiming
that delayed publication cannot occur.

**Confirmed:** single_worker.worker_operations is instantiated per pooled
worker; stage_execution.operations_from and StageExecution.release/_closers
own the deployment and its actual teardown. A one-per-deployment ingestion
resource needs exact wiring there, outside the current five-path packet, or a
concrete equivalent proving the same ownership. The review proposes injection
of a bounded enqueue capability through the existing serving-only runtime
refresh seam, with an independent ingestion-thread store handle; this is design
support for owner selection, not implementation authority. Numeric scanner and
manager-stop limits, cross-composition no-replacement and safe fixed staging
creation/recovery remain unspecified. Return baton.ops with the finite list.

Evidence review-evidence-174739.json pins source/design hashes. Design review
only;0s tests/probes/runtime execution, no product/test/PROGRESS/Git edits.
The minimum/v13 boundary and W2 gate remain unchanged.

## 2026-09-15 — owner pins delayed-final-count semantics and the composition boundary (M174788)

Slawomir selected the **delayed-final-count semantics**: an update admitted
while the operation was live may arrive after completion; its timestamp is
**manager receipt time** and is never evidence of continued provider activity
and never authority to change terminal state. The terminal precheck is a cheap
early skip, not a correctness boundary, and the viewer reports activity as
historical once the stage is terminal.

Also selected: the additional **`v12/python/tools/stage_execution.py`**
composition boundary, owning one ingestion worker per deployment with its own
thread-opened `ControlStore` handle, released through `StageExecution._closers`;
the `single_worker.refresh_runtime` enqueue hook; trusted seven-member enqueue
binding; no replacement across recomposition while a prior worker is unresolved;
numeric scan/overflow limits; a nonblocking baseline whose failure leaves
activity unknown; and exclusive `O_CREAT|O_EXCL|O_NOFOLLOW` staging that
suppresses rather than cleans up.

Completed packet: `ACTIVITY-DOCUMENT-DESIGN-174799.md`. Design only.

## 2026-09-15T04:06:59Z — review174872: retained decisions and concrete remainder

Reviewed design174799 SHA256401637e167c2e76cceebb6846b1c7d683189751ee0df6ca7d8954143a628890e
under owner174788. Delayed-final-count receipt semantics explicitly supersede
the old demand for strict same-operation late-write revocation. New composition
scope, numeric bounds and exclusive/no-follow suppressing staging are accepted
design directions, not product implementation. Do not reopen these selections.

**Confirmed:** bootstrap uses single_worker.operations_from/_Operations.close,
not stage_execution.operations_from/StageExecution._closers. The packet's
both-covered-by-one-constructor claim is superseded by this source correction.
**Inferred:** a synchronous baseline scan can stall in one filesystem operation
despite entry/depth caps, and an instance-local closer cannot prevent a distinct
new composition starting a replacement for an unresolved ingestion helper.
Review `review-2026-09-15T04-06-59Z.md` names three finite mechanism completions
within the selected source paths; these are not executed product reproductions.

Keep the manager-local event root out of the wire document and distinguish its
six content identity fields. Existing viewer job_viewer.py still renders activity
UNKNOWN; its historical-after-terminal display rule needs coordination through
W167896, not a claim of implementation or silent source expansion here.

Evidence review-evidence-174872.json pins design and sources; prior nine source
hashes unchanged. No tests/probes/live execution (0s), no product/test/PROGRESS/
Git edits. Return baton.ops for completion disposition. Work remains design-only,
unfinished and a W2 gate; rich UX/v13 deferrals stand.

## 2026-09-15T04:16:56Z — owner174917 routing and review174947 corrections

Owner174917 selected completion of baseline admission, separate pooled/bootstrap
ownership and shared bounded admission within existing scope, design only.
Further in-scope corrections go directly to baton.impl and back to baton.feat;
baton.ops is reserved for a concrete new scope/product decision or the completed
implementation-selection packet. This supersedes the earlier routine ops return.

Reviewed ACTIVITY-DOCUMENT-DESIGN-174920.md SHA256
3731daca7a8b196ea1cd97cf34df8c8b88af691271ba2e8818b634683d3443ef.
**Accepted:** separate actual constructor/closer hooks, retained registry owner
direction, six wire fields distinct from local root, no diagnostic adoption and
honest viewer follow-through. Transport/count semantics/numbers/staging stand.

**Inferred design counterexample:** old file1000 bytes plus10 appended before
the first tick has1010 bytes and new mtime. The proposed timestamp discriminator
counts all1010, so its claim to reconstruct a correct baseline is superseded.
Use a true completed baseline or construction-proven fresh/unrestored emptiness;
otherwise optional activity stays unknown. This is reasoning, not a runtime test.

**Confirmed composition mismatch:** the selected helper is per deployment,
whereas the new registry is per attempt and the new root operand is fixed once
at construction. Specify deployment/store helper admission plus per-attempt
trusted root/identity requests. A manager-local queued root was never forbidden;
only a wire-supplied host root and synchronous diagnostic adoption are excluded.
Review `review-2026-09-15T04-16-56Z.md` gives exact corrections and lifetime rules.

review-evidence-174947.json pins ten unchanged source hashes. Static review
only,0s tests/probes/live execution, no product/test/PROGRESS/Git edits. Return
directly baton.impl to finish the coherent design, then baton.feat. No
implementation selection or W61599/W2 completion is asserted.

## 2026-09-15T04:23:56Z — review175005 accepts baseline; helper admission still due

Reviewed design174971 SHA25622427e63b215578d5e911235a33347856b3214edcae35b8fe222c2fce14f1d85.
Construction-proven fresh/unrestored baseline with unknown on injected/reused/
restored homes resolves the mtime objection; per-request trusted roots resolve
the fixed-root composition mismatch. Preserve those accepted corrections.

The per-attempt registry still does not exclude replacement helpers: C1/H1 can
remain blocked for (S,A) while C2/H2 acquires (S,B). The claim that separating
helper and admission names resolves the retained no-replacement requirement is
superseded to this extent. This is a reasoned design sequence, not a runtime
reproduction. Add the helper-level deployment/store slot before thread start,
retained until positive termination, and test different-attempt recomposition.
Review `review-2026-09-15T04-23-56Z.md` gives the exact in-scope correction.

Return directly baton.impl under owner174917, then baton.feat. No new owner
decision or product scope is needed for that correction. All other accepted
design decisions and W167896 viewer follow-through stand. Work remains design-
only and gates W2. review-evidence-175005.json pins ten unchanged source hashes;
verification execution0s, no tests/probes/live execution or product/test/
PROGRESS/Git edits by reviewer.

## 2026-09-15T04:29:53Z — review175051 accepts completed design for selection

Design175025 SHA256014be97ecf91807fde86d1d84c0d05ede70b3bdd12790a23e3abc3ee57e99906
resolves the final helper-exclusion objection. Both factories acquire one
process-wide ownership slot per held control-store identity before helper
start, without an attempt id in the key. An occupied slot suppresses the new
helper and all its ingestion, including requests for a different attempt.
Positive termination releases the slot; failure before any helper starts may
unwind it. The ingestion thread closes its own handle during finalization,
while a timed-out closer leaves the handle/slot untouched and reports the fact.

This explicitly supersedes the earlier per-attempt helper-admission design and
remaining changes-requested status. Fresh/unrestored baseline, per-request
trusted roots/identities, transport, receipt semantics, numbers, staging, both
factory hooks and W167896 viewer follow-through remain accepted. Review
`review-2026-09-15T04-29-53Z.md` consolidates the current corrected chain and
six-source/five-test selection packet so historical contradictions are not
implementation instructions.

Pass baton.ops for owner implementation selection under owner174917. This is
design acceptance only: no product implementation, executed runtime acceptance,
Work closure or W2 release is asserted. No correction remains from the
controlling design reviews; implementation still requires its focused tests
and independent candidate review. The rich-UX/v13 boundary is unchanged.

review-evidence-175051.json pins the complete design chain and ten unchanged
source hashes. Verification execution0s; no tests/probes/live provider/engine
execution or product/test/PROGRESS/Git edits by reviewer.

## 2026-09-15 — the activity source is implemented (claim 177898)

The selected design is implemented over its six source paths. Two facts from
this round are worth keeping beyond the candidate:

**The outer `docker exec` stderr was never the provider's stream.**
`ClaudeAgent` runs the provider with stdout on a private anonymous pipe it
reads inside the container and stderr on `DEVNULL`, so the count this manager
published was of the worker's own transport noise — a silent provider grinding
for ten minutes looked identical to a stopped one, and a chatty exec wrapper
looked alive. That is why the source had to move inside the container, and it
is the whole reason the first review of this Work rejected the original wiring.

**A baseline that is measured cannot be trusted; one proved by construction
can.** An uninjected `_scratch` is a `mkdtemp` this process just created, so
its private `.claude` is provably empty of native files with no scan and no
stat — a true pre-launch zero that costs the launch nothing. Every other home
is **unknown**, and nothing is estimated. The mtime rule that preceded it was
wrong for a reason worth recording: 1000 bytes with 10 appended has 1010 bytes
*and* a fresh mtime, so mtime can say that a file changed and never how much of
it is new.

**Three reversal probes came back as non-evidence** and the tests they exposed
were corrected — a truncation case that asserted only that a total had not
fallen, a positive-total case whose `None` was being absorbed by the
publisher's own dedup so a **zero** would have been published, and an
observer-fault case that proved nothing because a turn survives a dead
publisher thread either way. A probe that passes with its guard removed is not
a test of that guard.


## 2026-09-15T13:33:05Z — owner hard stop at 100 minutes of claim177898

Slawomir directs a hard stop at 100 minutes for W61599, then joint review of the current state before further work. Claim177898 began 2026-09-15T12:15:43Z. The deadline is therefore **2026-09-15T13:55:43Z (07:55:43 America/Denver, MDT)**. This is an owner-selected wall-clock execution boundary, not a cumulative test-accounting gate. It supersedes open-ended continuation of this claim and automatic further W61599 correction cycles pending that review; it does not change accepted behavior or declare a candidate accepted.

Claude should budget the remaining interval to stop execution, terminate/clean up owned test processes, preserve current bytes and evidence, and return a concrete handoff by the deadline. Record completed scope, actual passing/failing checks and measured/unknown costs, exact unfinished scope, any remaining processes/resources and blockers. Do not start work that cannot finish and clean up before the deadline. Return control to baton.ops through the supported route for owner review; if route authority requires another destination, state the stop ruling and do not resume implementation automatically. Do not begin queued preparation after this stop until the owner has reviewed the state. No claim release by the prompt participant or forced process termination is performed by this record.

The owner said he will terminate the process if necessary. A conversational notification is not an enforced OS deadline and may not be consumed during an active turn. Any forced stop must target the then-current exact executor, not assume that an old bridge PID identifies only this Work. A later recovery must re-read the claim and resource state; killing a process is not proof that its claim or child processes were cleaned up.


## 2026-09-15 — owner defers reported pre-existing suite failures until post-v12

After W61599 implementation handoff178359, Slawomir directed: "the so called 'preexisting' failures need to be addressed in post-v12 era, where we have speedy access to parallel work. I don't want to burn time on them now".

Record the baseline failure backlog under W165786 for bounded parallel work after v12 readiness. W61599's ACTIVITY-IMPLEMENTATION-177898.md reports baseline7259 tests/89 failures-errors and candidate7333 tests/88 failures-errors, with the remaining set reported unchanged from baseline. These are author-reported classifications, not an independent certification or a green suite. Preserve the existing results, failure identifiers/log locators where already available, and the exact baseline/candidate context. Do not spend current release time repairing those baseline failures, reconstructing broad suite history, or repeating full suites merely to investigate them.

The active W61599 reviewer should use existing evidence and focused checks of the changed behavior and any concrete suspected introduced regression. Candidate acceptance does not require fixing unrelated baseline failures. Report a concretely demonstrated defect in selected v12 execution separately; do not call a new regression pre-existing to waive it, or use speculative classification concerns to launch a baseline cleanup campaign. This ruling narrows current verification/repair scope, not truthful result reporting or independent acceptance.

After readiness, W165786 will decompose surviving failures into small Jobs with explicit file ownership, prioritization and acceptance, reusing v12 parallel execution. Reuse existing defect Works when identified; no new implementation/backlog copies or release-gate edges are created now. The downstream consumer must revalidate the surviving failures then rather than treating this snapshot as current indefinitely.

Evidence: baton:work/records/2026/09/finding-live-worker-log-observability/ACTIVITY-IMPLEMENTATION-177898.md, section8; PROGRESS.md claim177898; W61599 pass178359. This explicit post-v12 repair selection supersedes any interpretation that the baseline suite must be made green before W61599/W2 can proceed. W161234 and the already-selected required v12 outcomes remain independently accountable.

## 2026-09-15T13:39:06Z — current-state review returns to owner under stop ruling

baton.codex claim178362 performed bounded static review after implementation
pass178359. The later OWNER-STOP-177898.md ruling requires joint owner review
before further work and supersedes automatic correction dispatch. Return baton.ops,
not baton.impl; no queued preparation or new correction cycle is selected here.

review-2026-09-15T13-39-06Z.md records: two current test hashes differ from the
submitted handoff; the enqueue adds realpath/lstat work on the serial serving
path; both stop methods discard their thread reference before a timed-out join,
so a second stop can falsely report success; and path-based directory scanning
can follow a link substituted after its no-follow check. Source/control-flow
findings are distinguished from an inferred directory race; no dynamic probe
was run. No candidate acceptance or shared-path release is granted.

review-evidence-178362.json SHA256
b4ad2a0eca2f394afb0bddc4e79f50d625fa44c8d6d81c6c98e29fa7328d34d2 binds all12
current/submitted comparisons. All six source hashes match. Test drift authorship
is unknown. The author's aggregate suite/reversal claims lack bound logs,
failure-identity comparison and process-cleanup evidence; they remain reported,
not independently accepted. Approximately2966s includes an approximately190s
estimate, which must retain that qualification. No stopwatch replenishment gate.

Reviewer verification0s; no product/test/PROGRESS/Git changes or test processes.
Owner reviews the stopped state, evidence/resources and concrete next assignment.
This supersedes pending implementation acceptance/automatic return as next action,
not accepted product semantics, prior history, W167896 viewer ownership, W161234
shared-file order or W39649/v13 deferrals. W61599 remains unfinished.

## 2026-09-15 — owner178421 selects bounded tuner correction, claim178427

Owner reroute178421 explicitly assigns baton.tuner the three source corrections
in review-2026-09-15T13-39-06Z.md: remove diagnostic filesystem resolution from
the serving loop, retain truthful repeated-stop results, and prevent directory
replacement from attributing foreign native activity. This supersedes the
OWNER-STOP-177898.md hold only for this correction. Return baton.feat for focused
independent review, then baton.ops; no automatic further implementation cycle.

Revalidated all12 current file hashes against review-evidence-178362.json.
correction-178427/base.json and its immutable base snapshots preserve those
bytes, including the two test files differing from the older submitted hashes.
Earlier suite/probe results are not rebound to these bytes. Requested known
final edits/snapshots/process disposition from the author in T61599 M178453;
unknown historical facts remain unknown and no broad reconstruction is selected.

Tuner owns exactly claude_agent.py, baton_worker.py, tools/single_worker.py and
their existing test_claude_agent.py, test_exchange.py, test_single_worker.py
paths in the selected v12 tree, plus this dossier. Tests cover no filesystem
resolution at enqueue, repeated timed-out stops with retained handle/slot and
positive cleanup, and root/child-directory replacement races with descriptor
cleanup. Standing test authority applies; expectation changes and reasons will
be in the handoff. Preserve limits, fresh-home baseline, unknown reused HOME,
optional transport, lifecycle bytes, receipt-time semantics and both factories.

Only focused deterministic regressions and process-cleanup evidence are selected.
No full suite, baseline repair, architecture redesign, broad historical accounting
or live provider/engine execution. W161234 shared-source release still awaits
independent acceptance; W167896 viewer follow-through and v13 deferrals stand.

## 2026-09-15 — bounded correction complete, tuner claim178427

HANDOFF-178427.md and correction-178427/candidate.json bind the exact correction
and retained base/candidate bytes. The three review178362 defects are corrected:
filesystem resolution is off the enqueue thread, repeated stops retain their
thread handles, and directory traversal uses no-follow parent-relative descriptors
with opened-object checks. This supersedes the old implementation claims that
enqueue did no filesystem work and entry checks alone excluded directory races.
A missing/inaccessible native root now conservatively freezes optional activity.
Accepted baseline, transport, counts, receipt-time semantics and scope stand.

Author M178528 supplied exact submitted test snapshots. Both old hashes verify;
the two retained diffs prove six author test corrections after his hash list.
Current correction hashes are separate. Fresh final focused verification passes
82 tests; 17.160464063985273s total new supervised execution including failed
setup/negative runs. Every owned group exited, with no live test threads in the
completed checks. See handoff for negative-control qualifications, ambient
dependency versions, retained author logs and attributed historical cleanup.
Return baton.feat for focused independent review then baton.ops, per178421.
No automatic correction cycle, W161234 shared-file release or viewer completion.

## 2026-09-15T14:06:58Z — correction178427 independently accepted

baton.codex claim178572 accepts the bounded source/transport/ingestion candidate
in correction-178427/candidate.json SHA256
acabca2d229f984a647626d6feb5244d4d1d0bea95c80b025f802ca9194138b3.
review-2026-09-15T14-06-58Z.md SHA256
975d4ea565eb3eae50e5f053b7677fdeae00a5109f518502331d06ad27a42e90 and
review-evidence-178572.json SHA256
4f98daa2c62ba459b7ffebbd5479a610d78d34d86f6202cff243dc92789832cd bind the
independent outcome. All12 candidate/base comparisons, repository modes/types,
and56 inventoried evidence hashes verified; final candidate bytes remained fixed.

The three review178362 defects are resolved: no diagnostic path resolution on
enqueue, truthful repeated stops with retained thread handles, and descriptor-
relative no-follow traversal with child identity checks. The two stale submitted
test hashes are reconciled to retained exact snapshots and six author corrections;
this supersedes their unknown-authorship classification, not the historical review.
The independently run focused82 tests passed with zero failures/errors and no live
test threads. The owned process group was absent; no termination was needed.
Measured reviewer supervisor time7.170285156025784s. See the review for exact
virtual-environment dependencies, test expectation assessment and evidence limits.

Author correction17.160464063985273s and original approximately2966s (including
approximately190s estimated) remain separate. Historical author process cleanup
and baseline89/candidate88 pre-existing classifications remain attributed claims;
no broad rerun, baseline repair or historical reconstruction was performed.

This supersedes pending independent acceptance as the current action. Return
baton.ops under178421 for owner disposition, with no automatic further implementation.
W161234 has an accepted exact shared-byte reference but still needs explicit
ownership release. W167896 historical terminal viewer follow-through remains;
visible count delivery and Work closure are not asserted. W165786/post-v12 baseline
repair and W39649/v13 richer viewer scope stand. No product/test/PROGRESS/Git edits.


## 2026-09-15 — resume Claude's approved preparation after owner review

Owner review of the stopped W61599 state is complete: owner178644 accepted correction178427 and released shared files; owner178645 selected W161234 B for tuner. Slawomir now reports that Claude is not picking up work, in the context of the already-approved Claude-prepares/tuner-implements plan. Resume that selected preparation: W177937 viewer activity connection, then W177938 final correction/restart proof packet.

This explicitly supersedes OWNER-STOP-177898.md's temporary prohibition on these two queued preparation tasks and Claude's stop acknowledgment178462. The original implementation claim177898 ended before its deadline and is not resumed. No new W61599 producer edit, implementation, live experiment, broad suite or baseline repair is authorized. Claude owns only each preparation dossier and hands exact concrete execution packets to baton.ops for tuner follow-through. Revalidate accepted W61599 candidate/review and W161234 current state; do not edit tuner's shared source files or active dossier. Existing independent review and scope boundaries remain.


## 2026-09-15 — owner assigns remaining viewer delivery to tuner after Claude preparation

Slawomir requested that W61599 also be assigned and then asked to resume. The accepted producer correction178427 and owner acceptance/shared-file release178644 remain intact. The remaining W61599 delivery is the minimal viewer connection. Assign that outcome to baton.tuner after W177937 supplies the concrete viewer consumer packet; Claude prepares W177937 and then W177938 under the already-recorded resumption ruling. Preserve W161234 B shared-file ownership and the accepted producer bytes. No producer rewrite, rich viewer expansion, broad suites, baseline repair or live execution is selected.

W61599-on-W177937 is the proposed exact dependency: the viewer implementation consumes its concrete API/path/verification packet. This sequences existing selected work and is not another W2 release requirement or an architecture review. The owner should add this dependency while W61599 is at baton.ops, then route W61599 to baton.tune. The completed packet and accepted minimum monitor scope bound the implementation; record exact paths and coordinate any overlap before edits. Return the implemented candidate for focused independent review. These ledger operations are pending until confirmed, not claimed by this file.

Operational finding: at snapshot178674 all prior resume routing attempts remained uncommitted. Standalone canonical reroute writes as baton.prompt failed with sqlite3.OperationalError: attempt to write a readonly database; two requested escalated retries failed before execution with approval request failed. No database inspection, alternate identity, hidden mutation path or claim release was attempted. The resumption decision is pinned in the existing dossiers, but delivery through the CLI still needs the operator's normal authorized boundary. Human commands will notify Claude using poke (the Work is already routed to her), record the real viewer-preparation dependency and route W61599. The notification relays recorded owner authority and does not itself grant workflow authority.


## 2026-09-15 — owner selects parallel viewer implementation by Claude

Slawomir states that tuner is tied up and Claude can carry out one implementation. Snapshot178772 confirms tuner actively holds W177936 fixture preparation; W61599 and W161234 are ready/unclaimed on baton.tune, and Claude is idle. Select W61599's independent three-file viewer connection for baton.claude. This supersedes the tuner-only implementation assignment178690 for this remaining viewer slice; W161234 B and W177936 stay with tuner.

Input: owner-accepted W177937 PACKET.md SHA256 aaa30c9dd529d245f89b1d0645a00c85d5769a94b31b8b8d1411751646a7db28; preparation closed satisfying178761. Exact product/test ownership: v12/python/tools/job_viewer.py, v12/python/tests/tools/test_job_viewer.py, v12/python/JOB-VIEWER.md, plus this W61599 dossier for author progress/candidate/evidence. Read the packet and revalidate its three base hashes before editing. Consume existing stage.runtime.activity; positive live count with age, terminal historical instant, absent/invalid count unknown. Preserve snapshot staleness separately and no second backend read. These files are disjoint from tuner's active fixture and selected B paths.

Implement this bounded packet to completion, run focused tests.tools.test_job_viewer verification with the packet's finite timeout and cleanup, publish exact candidate and measured evidence, then pass baton.feat for focused independent review followed by baton.ops. No repeated architecture review, six-producer-path edit, new backend/schema, rich UI, broad suites, baseline repair or live provider/engine execution. The former W61599 claim177898 and its expired deadline are not resumed; this is a newly selected three-file implementation claim. Prior source acceptance and shared-file release remain intact. Canonical assignment remains pending until the reroute succeeds.

## 2026-09-15T14:42:20Z — viewer review178853 requests two corrections

baton.codex reviewed viewer-candidate-178777.json SHA256
2d8bd9bfe8e2769f1da33d9d5e89870c43d9ec2679482f122bbe5c698a1a37ad under
owner178775. review-2026-09-15T14-42-20Z.md SHA256
cefb901369782edfc1155bfc0c3c6eddca2bf997efce0f9ec287d4300d2c7650 and
review-evidence-178853.json SHA256
41b421f30c751d467a2428dbb21b43acd1685dc4deb996b6d4329c9564fe66f1 bind the
outcome. All three candidate bytes/modes and exact accepted viewer base hashes
verified; retained base/candidate copies and independent results are in this
dossier. Candidate bytes remained unchanged through verification.

R1: the default100-column list clips the new terminal activity timestamp and
entire stage identity on an ordinary completed stage. The new terminal test
checks full timestamp only in detail. Preserve both facts in the default list
with a bounded layout correction and test all three terminal states.
R2: a5659-byte valid JSON snapshot with activity integer10**400 passes parsing
then raises OverflowError in the new floating-point byte formatter. The old
constant-unknown behavior renders the same snapshot. Bound/validate the count
before conversion and cover the input-to-render path; this is malformed consumer
input, not a claim that the trusted producer emits an out-of-domain count.

Independent74-test focused viewer run passed, and both additional probes
reproduced. Measured reviewer supervisor3.266339145018719s, no timeout/test
threads, process group positively absent. Author main viewer run3.187675s and
five reversal probes remain attributed; probe durations are not supplied and
are not invented. Prior producer costs and baseline qualifications stand.

This supersedes pending viewer review/visible-count delivery claims as the
current action: return baton.ops for R1/R2 disposition, no automatic further
implementation. Accepted producer correction178427 and release178644 stand;
W161234 B owns its separate active paths. No producer edit, new backend, rich UI,
baseline repair, broad suite, live provider/engine, product/test/doc-candidate
change, author PROGRESS edit or Git mutation occurred. Only reviewer dossier
evidence/FINDING/PLAN changed. Visible-count acceptance and owner closure remain
pending; W165786/post-v12 baseline work and W39649/v13 scope are unchanged.

## 2026-09-15T15:04:29Z — corrected viewer independently accepted, claim179011

Owner reroute178927 selected the bounded R1/R2 correction within the existing
three-file viewer scope; that selection was pinned in PLAN before implementation.
It superseded the pending owner-disposition hold for this correction only.
review-2026-09-15T15-04-29Z.md now accepts viewer-candidate-178930.json SHA256
820c7c9b1aff17390b78d304d1d320dd8c13c3279823361f362be30b4cc314c7.

**Confirmed:** R1/R2 are resolved. The default list separates activity timing
onto a continuation line, preserving the original fixture's full stage identity
and terminal receipt instant. Domain validation precedes formatting, so an
oversized integer renders unknown while the largest valid count remains visible.
Independent83 focused viewer tests pass, plus12 actual-JSON renderer probes over
four states and normal/ceiling/oversized counts. All three file hashes/modes and
both prior base/candidate snapshot chains verify; bytes remained fixed.

viewer-review-179011.py, .json and .log retain the verification and exact copies.
Measured supervisor3.266575059009483s; no failures/errors, live test threads,
timeout or termination signals; owned process group positively absent. Prior
author/reviewer costs and unknown reversal durations remain separate in the
review. Historical baseline classifications remain author testimony; no broad
suite, baseline repair, live provider/engine or producer-path test selection.

This supersedes review178853's pending R1/R2 acceptance status. The minimal
viewer connection is independently accepted and visible activity rendering may
be claimed, combined with the already accepted producer correction178427 and
owner release178644. Return baton.ops under178927 for owner disposition; no Work
closure or deployment is asserted here. W161234 owns its separate shared paths.
W39649/v13 richer stream/viewer work and W165786/post-v12 baseline repair remain
deferred. Reviewer changed only dossier evidence/FINDING/PLAN, not candidate
source/tests/docs, author PROGRESS or Git state.
