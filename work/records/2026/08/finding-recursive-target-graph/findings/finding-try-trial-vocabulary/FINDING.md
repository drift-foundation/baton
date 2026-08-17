# Finding: use `try` and `trial` for candidate verification

## Discovery context

Discovered while reviewing W179's treatment of thread-less verification
assignments. The existing protocol calls the durable candidate-verification
object a `round` and creates it through the `round` command.

## Observed

`round` describes repetition but not purpose. A human reading it must already
know that the object asks one or more remote endpoints to exercise a staged
candidate and return evidence. It is also easy to mistake for another kind of
Work.

## Decision — 2026-08-16

The command is **`try`** and the durable object is a **trial**:

```text
try work=W50 candidate=build-17 assign=push.bug assign=web.bug
```

Human and agent projections describe:

```text
Trial 1
Candidate: build-17
Progress: 1/2
```

- `try` is the call to action: ask the assigned endpoints to try this exact
  candidate.
- A trial is structured evidence inside one existing Work, never a new Work
  type. It has no independent Current, phase, claimant, dependency graph, or
  dossier.
- `report`, `assess`, `extend`, and `abandon` retain their roles against the
  trial and its assignments.
- Reports and assessments never transition or close Work automatically.
- Work may close with a trial still incomplete; closure records the trial's
  candidate, received/assigned progress, observations, elapsed window and
  withdrawn pending endpoints.
- A separately accountable defect discovered during a trial becomes a new
  Work; the trial itself is not promoted into one.
- This is intentional heavy pre-release evolution. No compatibility alias for
  `round` and no migration of trial authorities is required.

## Acceptance

- CLI, JSON, TUI, documentation and workflow stories consistently use `try`
  for creation and `trial` for the durable object.
- The obsolete `round` command is refused as unknown rather than retained as
  an alias.
- Identifiers, projection fields and errors use trial vocabulary coherently;
  no mixed `round`/`trial` surface remains.
- Multi-assignee progress, replacement candidates, reports, assessments,
  extension, abandonment, close-time evidence and race guarantees retain
  their existing behavior.
- Focused source and packaged workflow tests cover one trial, multiple
  assignees, a replacement trial, incomplete close, and unknown `round`.

