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
