# Finding: the README falsely limits Baton to one repository

## Observed — 2026-08-18

The README opening says Baton coordinates humans and agents working in the
same repository. That is not Baton's model: teams coordinated by one authority
may work in different configured repositories and attach Work to evidence in
those repositories.

## Confirmed decision — 2026-08-18

Remove the same-repository limitation from the README opening. Describe Baton
as coordinating people, agents, teams, and models across repositories without
implying that one checkout contains every participating team.

## Acceptance

- The README opening no longer says or implies “same repository”.
- The replacement remains a concise product description rather than adding
  configuration or storage detail.
- Existing product-positioning tests remain green.

## Implementation revalidation — 2026-08-18

The current README still contains the exact false limitation in its opening
sentence. No other active public document found by the focused scan states a
same-repository constraint. The existing product promise immediately above it
already names people, agents, teams, and models, so the narrow correction is
to describe their collaboration as spanning repositories without adding
configuration or storage mechanics to the opening.

## Implementation evidence — 2026-08-18

The README now describes humans and agents as collaborating across
repositories. The focused documentation regression normalizes the opening's
Markdown whitespace, requires the positive phrase `across repositories`, and
forbids `same repository`. All eight public-documentation tests pass and
`git diff --check` is clean.

## Review clarification — 2026-08-18

The review return at Work event 273 asked the opening to name both the teams
and the work coordinated across repositories. The first wording removed the
false boundary but named only humans and agents in that sentence, leaving
teams and work to the tagline. The revised sentence makes the complete
cross-repository claim directly while retaining the short opening.

The strengthened regression now requires both `engineering work across
repositories` and `teams of humans and agents` in the normalized opening. All
eight public-documentation tests pass and `git diff --check` remains clean.
