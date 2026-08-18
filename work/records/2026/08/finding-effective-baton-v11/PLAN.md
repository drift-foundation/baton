# Plan

**Status — 2026-08-18:** post-W245 response delivered; returned for a new
review pass. W159 and W245 are both closed, so the guide and its executable
proof describe the final grammar AND the final route / nullable-current
contract. W3 remains later, separately gated
vocabulary work; this guide uses the current `Thread` vocabulary deliberately.

1. [done] Derive the operating sequence from confirmed v11 findings, current
   CLI help, and the tested workflow battery; record the model and acceptance
   boundary in `FINDING.md`.
2. [done] Replace the protocol-10 guide completely. Lead with the minimal
   setup and straight-through Work lifecycle, then explain Current, Next,
   phase, claim, readiness, waiting, parking, containment, dependencies,
   discussion, obligations, trials, terminal outcomes, and recovery in that
   operational order.
3. [done] Add the six required workflow examples from `FINDING.md`, using
   short copyable commands and showing the decisive canonical JSON facts after
   each transition. Revalidate all grammar against the tree after W159 and use
   the current `Thread` vocabulary; W3 will update that vocabulary later.
4. [done] Integrate permanent dossier/root practice, one-writer progress,
   append-only review, explicit operation identity/retry, and the one-readiness-
   consumer rule. Remove every v10 message/notice/claim/materialize command and
   every suggestion that v10 is a fallback.
5. [done] Keep the guide subordinate to the protocol and shipped
   quickstart: link to detailed contracts instead of duplicating schema or an
   exhaustive command reference. Check its terminology against W103's public
   documentation rewrite.
6. [done] Execute every command example against the built v11 artifact in a
   fresh coordination home, run focused documentation/package checks and
   `just test-v11`, then return the Work for independent review with the exact
   release/digest and evidence paths.
