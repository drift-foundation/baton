# Publish a provider failure reason without publishing the bearer

Work: W55360
Origin: W51487 run2 finding 2, repeated by run5/run6 finding 2

## Finding

The real Claude adapter currently publishes only the provider process's exit
status. That is intentionally safe but operationally insufficient: W51487
needed credential-free probes outside two separate supervised rounds to narrow
status 1, and the second round still could not distinguish a credential that
stopped being accepted from an account-level refusal.

The provider CLI already has a safer structured signal. With
`--output-format json`, an invalid invented credential produced a stdout JSON
document containing:

```json
{"is_error": true, "duration_api_ms": 0, "terminal_reason": "api_error"}
```

The evidence does not authorize copying that document or any provider-authored
text. It supports reading only a bounded provider stdout record, mapping an
exact structured member to this adapter's own closed vocabulary, and
publishing only the mapped word.

## 2026-08-31 reviewer revalidation

**Observed.** W55360 had no canonical dossier binding when claimed. Its sole
thread message points to the append-only W51487 acceptance records and run5
diagnosis. This record is the permanent dossier reconstructed from those exact
references.

**Observed current boundary.** `v12/worker/claude_agent.py` composes:

```text
claude --print --permission-mode acceptEdits <prompt>
```

`ClaudeAgent._ran` sends stdout and stderr for both the provider and the
provider-edited verification command directly to `subprocess.DEVNULL` and
returns only the exit code. `_provider` then writes the numeric status and a
fixed explanation into `proposal/result.json`; `_disposition` carries the same
explanation into the worker recap. The focused adapter suite is green at 68
tests.

**Confirmed historical decision.** W39357's accepted fifth-round rule is
stronger than “do not publish diagnostics”: no byte either child writes is
read at all. It deliberately deleted every capture buffer and ceiling after a
provider stderr containing bearer material reached both `result.json` and the
protocol recap. That record explicitly says diagnostic recovery requires a
separate later-pass Work and an explicit operator-authorized decision.

**Confirmed interaction.** W55360 cannot be implemented as bookkeeping. It
must explicitly supersede the W39357 no-read rule for one crossing only:
provider stdout when the adapter invokes the CLI in structured JSON mode.
Provider stderr and both verification streams remain on `DEVNULL`. No
provider-authored byte is durable evidence or returned protocol content.

## What the evidence can and cannot say

**Confirmed.** The one observed provider value is `api_error`. An exact map
from that value to the adapter-authored word `api-error` is safe to publish if
all other values and malformed records become one fixed fallback such as
`unclassified`.

**Confirmed limitation.** `api_error` does not distinguish credential expiry,
invalid scope, account limit, or every possible network/API failure. W51487's
invalid-credential probe and its account-limit hypothesis fit the same
observed category. W55360 can publish a more useful terminal category; it
cannot honestly publish the causal credential diagnosis its originating
rounds wanted.

**Out of scope.** Classifying raw diagnostic prose with patterns like
W17110's `trial.mjs` would be a different and wider security decision. That
classifier reads raw provider text; W55360's submitted remedy instead names
the structured `terminal_reason`. Do not silently widen from one to the other
to obtain finer categories.

## Proposed safe boundary

This is decision support pending the approval below, not implementation
authority.

1. Add the CLI's exact structured-output operands to the provider argv. Keep
   the prompt last and retain the existing closed environment.
2. Capture provider stdout through a continuously drained pipe with a fixed
   retained-byte ceiling. Keep at most the ceiling plus an overflow sentinel
   in adapter memory and discard every later byte while the child continues,
   so a verbose provider cannot block on a full pipe or allocate an unbounded
   result. Do not create a capture pathname or a host-visible file.
3. Leave provider stderr on `subprocess.DEVNULL`. Leave both verification
   streams on `subprocess.DEVNULL`; verification is provider-edited code and
   has no structured signal this Work needs.
4. After a nonzero provider exit only, parse the complete, non-overflowed
   stdout as one UTF-8 JSON document. The root must be a plain object with one
   unambiguous string `terminal_reason`. Invalid UTF-8, malformed/trailing
   JSON, duplicate keys, a non-object, missing/non-string reason, overflow, or
   an unknown value maps to the fixed adapter word `unclassified`.
5. Start with only the evidence-backed exact map
   `api_error -> api-error`. Any later provider value requires its own observed
   evidence and an explicit table/test change; substring or regex matching of
   the structured value is forbidden.
6. Publish the adapter-owned word in a new closed `failure_reason` member of
   the proposal's `provider` record. Compose `why` and the worker recap only
   from that word, the numeric status, and adapter-authored prose. Never
   interpolate the source value, the JSON document, parser errors, byte
   excerpts, unknown keys, or provider stderr.
7. A zero exit does not publish a failure reason. Timeout and start failure
   retain their current adapter-authored explanations; if the field is present
   for them, its values must also be fixed vocabulary (`timeout` and
   `start-error`) rather than exception text beyond the already accepted type
   name.

The implementation may choose a simpler pipe/drainer arrangement, but it must
hold the three properties above: bounded retained memory, continuous draining
to child completion, and no raw byte reaching a durable or returned sink.

## Required security regressions

- The exact provider argv opts into JSON and remains otherwise closed.
- A nonzero provider returning the observed `api_error` publishes only
  `failure_reason: "api-error"`; the raw spelling `api_error` is absent from
  every proposal file and the returned recap.
- Unknown values, malformed JSON, invalid UTF-8, duplicate
  `terminal_reason`, non-string values, trailing data, and over-ceiling output
  all publish only `unclassified`.
- A distinctive bearer marker placed in every other JSON member, member name,
  nested value, unknown terminal reason, and bytes after the ceiling appears
  nowhere in the proposal or returned answer.
- The same attack is driven through a real child writing provider stdout in
  multiple chunks; a fake returning a prebuilt buffer does not prove fd
  plumbing or bounded draining.
- A successful provider that writes the marker to structured stdout still
  completes normally and publishes none of it.
- A provider writing the marker to stderr remains protected by `DEVNULL`.
- Provider-edited verification writing the marker to both streams remains
  protected by `DEVNULL`; W55360 must not weaken the existing verification
  regressions.
- The overflow case proves the child is fully drained and does not deadlock,
  while retained memory never exceeds the stated ceiling plus its sentinel.
- Existing timeout, missing executable, nonzero exit, no-change, and verified
  candidate dispositions remain distinct.

## Open approval required before implementation

Does creation of W55360 authorize the narrow supersession above: read a
bounded structured provider stdout document in the default supervised path and
publish only an exact adapter-owned category?

The reviewer recommends **yes, narrowly**, because the Work exists after the
recorded diagnostic cost became real twice, the submitted remedy is a closed
mapping rather than passthrough, and the proposed regressions retain the
original publication boundary. Approval must also accept the honest result:
the first supported category is `api-error`, not `credential-expired` or
`account-limited`.

If approval requires causal credential/account diagnosis, stop and define a
separate raw-diagnostic classification boundary; do not claim structured
`terminal_reason` can provide facts it has not provided.

## 2026-08-31 — approver ruling: narrow supersession approved

**Approved by `baton.slaw` in W55360 return event 55479.** Default supervised
execution may read provider stdout only when the adapter has selected the
provider's structured JSON mode, and only through the bounded in-memory,
continuously drained boundary described above. The parsed value crosses no
publication boundary directly.

The initial closed map is exactly:

```text
api_error -> api-error
```

Malformed or trailing JSON, invalid UTF-8, a duplicate, missing or non-string
`terminal_reason`, an unknown value, or retained-output overflow maps to the
single adapter-owned word `unclassified`. No raw provider byte, raw member
name or value, parser detail, provider stderr, or verification output may
become durable or returned content. Provider stderr and both verification
streams remain unread on `subprocess.DEVNULL`.

`api-error` is descriptive only. It is not evidence of credential expiry,
account limitation, scope, or network cause, and documentation and returned
prose must not turn it into one.

This ruling explicitly and narrowly supersedes W39357's fifth-round no-read
rule for structured **provider stdout only**. The dated supersession is also
appended to W39357's owning finding. All other stream and publication safety
decisions in that record remain authoritative.

## Acceptance

- The W39357 finding contains an explicit dated supersession limited to
  provider structured stdout; its stderr and all verification output remain
  unread and unpublished.
- Only the closed adapter vocabulary is durable or returned. No provider JSON,
  raw terminal reason, diagnostic text, parser detail, or bearer marker reaches
  `result.json`, any other proposal file, or the worker recap.
- Capture is bounded and continuously drained, including overflow and chunked
  real-child cases.
- The proposal schema exposes the mapped failure reason and preserves current
  status/bound semantics.
- Documentation says `api-error` is descriptive and not proof of a credential
  or account cause.
- The focused adapter suite and adjacent worker-image/worker transport gates
  pass without a live credential. Any live confirmation remains a separately
  authorized supervised attempt.

## 2026-09-01 — clarification: the drain bound is independent of EOF

The acceptance above says capture is "bounded and continuously drained". The
independent security review (`review-2026-09-01T03-35-56Z.md` [P1]) showed that
this was not sufficient as written, and the clarification is recorded here
because a later reader will otherwise read the original bullet as satisfied by
a reader that waits for EOF.

EOF on the read end arrives when the LAST writer closes it. Any descendant the
provider starts inherits the write end, so a provider that spawns a long-lived
child and exits leaves an EOF that never comes — which suspends the adapter
after the provider is gone and past `PROVIDER_SECONDS`. `subprocess.run` kills
only its DIRECT child, so the timeout path has the same exposure.

**Clarified acceptance.** Completion of the drain is bounded independently of
EOF: the reader stops a fixed grace after the provider PROCESS ends, whatever
any descendant still holds. A stream not proved finished inside that grace is
a PARTIAL record and publishes `unclassified`, exactly as an over-ceiling
record does. Nothing about the approved read boundary widens: this is a bound
on waiting, and no additional byte is read, retained or published.

**Clarified acceptance.** The parser is total as well as strict. Python's
non-standard `NaN`/`Infinity`/`-Infinity` extensions are not JSON and are
refused, and a bounded record whose nesting exhausts the decoder answers
`unclassified` rather than raising out of the adapter. A bound on bytes was
never a bound on parser depth, and "every unusable document becomes
`unclassified`" is only true if the function has no third exit.

Neither clarification supersedes the approver ruling above; both are properties
that ruling's own words already required and the first implementation did not
yet hold.

