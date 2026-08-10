# Finding — TUI subject edge-whitespace courtesy

**Status:** premise corrected and direction re-ruled by Slawomir on 2026-08-10.
Implemented in the protocol-9 TUI. The shared core and agent CLI remain strict;
this is resolved outside the protocol-10 bundle.

## What the review found

The original finding claimed an edge-padded subject was already accepted and
stored after silent trimming. That was false. `validate_subject` in the shared
core has long refused leading or trailing whitespace, and the frozen oracle
has the same rule:

```text
"  Review result  "  ->  refusal: subject must not have leading or trailing whitespace
```

Nothing was being silently rewritten or stored differently from what an agent
submitted. Changing the shared core to trim would have weakened a deliberate
refusal and changed effectively-once identity: two requests that cannot both
reach retry comparison today would become the same request. That is not the
ruled direction.

## Current contract

The split is intentional:

- The TUI trims leading and trailing subject whitespace when the human sends
  from compose or reply. It uses the language's ordinary `str.strip()` and
  preserves all interior whitespace.
- A TUI subject containing only whitespace becomes no subject, exactly like
  an untouched optional subject field. The existing rule that a message still
  needs subject or content remains unchanged.
- After that narrow authoring courtesy, the shared core remains the sole
  validator for controls/newlines, byte length, emptiness, and every other
  authority rule. The TUI does not pre-empt or sanitize another refusal.
- The shared core and agent CLI continue to reject any subject with leading or
  trailing whitespace. An agent producing it has a bug worth reporting rather
  than hiding.
- Retry and manifest identity use the exact subject actually submitted to the
  core. The TUI submits the trimmed spelling; the authority does not merge a
  later padded spelling with it because that padded request is still refused.

This keeps the human text field forgiving without changing protocol semantics
or teaching the agent-facing API to rewrite input silently.

## Superseded — do not restore

The 2026-08-09 draft put trimming in the shared core, treated padded and
unpadded retries as identical, and scheduled the change for protocol 10. It
was based on the incorrect premise above and is superseded in full. The TUI
and CLI deliberately do not expose the same authoring convenience; their
different boundaries are the point of the corrected ruling.

## Coverage

- TUI compose and reply trim leading, trailing, and both-edge whitespace at
  send;
- TUI preserves interior whitespace;
- TUI whitespace-only subject becomes an omitted subject;
- the shared core still rejects the untrimmed spelling;
- newline/control and length validation remain core-owned;
- packaged TUI coverage demonstrates the human path while the same test pins
  the unchanged core refusal.
