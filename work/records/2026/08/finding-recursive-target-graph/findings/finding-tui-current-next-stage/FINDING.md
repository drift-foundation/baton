# Finding: Current and Next should name workflow stages

## Observed — 2026-08-16

The fresh v11 TUI rendered active feature implementation as:

```text
Current       Next
baton.impl    baton.feat
```

`baton.feat` is the exact endpoint that will receive the pass, but it does not
answer the operator's list-view question: what happens next? In the accepted
configuration that endpoint resolves through route `rview`, role `rview`, to
handler `codex`. The endpoint makes an upcoming review look like another
feature classification.

## Confirmed presentation ruling — 2026-08-16

**Confirmed by Slawomir.** TUI Work-table `Current` and `Next` are workflow
stage columns. Render each resolved endpoint's route handle, not its endpoint:

```text
Current  Next
impl     rview
```

The same rule applies to both columns: `Current` answers what is happening now;
`Next` answers what happens after the current stage. A null destination remains
`-`. A configured endpoint that does not currently resolve to a live route
must render an explicit unresolved marker rather than pretending its endpoint
kind is a stage.

This is presentation only. Canonical JSON retains the complete structured
endpoint object with `endpoint`, `route`, `role`, and `handlers`; commands and
passes continue to name endpoints such as `baton.feat`. Work details may show
the richer endpoint/resolution facts for diagnosis. The table does not erase
or rewrite authority state.

Team-local home views need only the route handle because the owning team is
already explicit context. A future multi-team table must qualify the stage by
team without changing the canonical object.
