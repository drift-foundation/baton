# Current checkpoint — shutdown-on-handoff specification signed

Work W274875. Author: baton.prompt, 2026-09-26. Canonical events read through
275184 (Claude's amendment signoff returned to owner); discussion through275131;
snapshot275193. W270664 returned to owner at274959, NOT accepted.

## Selected decision and current outcome

Owner approved the recommendation: governed resource mutations, including
maintenance deletion/reset, execute in token-bound Docker containers. The host
grants/enforces tokens and may explicitly renew only an unexpired token for the
same execution. Expiry/revocation cannot be reversed. FINDING's 11:57Z entry and
message275027 pin this, superseding the first draft's unanswered choices.

The previously signed DESIGN addresses all three findings in
`review-2026-09-26T11-52-40Z.md`: custody responsibility versus execution placement,
token-bound maintenance/reset and its finite host-supervision boundary, and
holder versus host clock/renewal authority. FINDING contains the response map.
Sections17/19 add the selected conformance obligations and policy. AGENTS and
v12/README now point to the v12 specification, preserving existing policy and
historical proof instructions.

Owner subsequently selected confirmed shutdown of the exact outgoing container
before every normal ownership handoff, including maintenance, review and
correction. The final FINDING entry and message275131 pin the decision and
explicitly supersede the inquiry-only status and unspecified normal-return
mechanism. Preserve durable context/workspace and restore in a fresh execution;
same-assignment renewal remains allowed. Live-container mount handoff is deferred
from v12; accepted experimental evidence is preserved. No product implementation
or runtime execution is selected by this document amendment.

## Exact signed candidate

| Path | Bytes | SHA256 |
| --- | ---: | --- |
| `v12/DESIGN.md` | 59518 | `7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0` |
| `AGENTS.md` | 36742 | `e6183efeaf5bf8045affe91bd983eff1e98c874334058bdb9fda0b56e080b2a6` |
| `v12/README.md` | 20289 | `87579686ae983818370866669c54f5ef44f45acd1c719208498663c3e09555ae` |

All DESIGN local links resolve; requirement IDs are unique; no trailing whitespace;
Both `git diff --check` and `git diff --cached --check` pass. All three candidate
files were re-measured at this checkpoint. No runtime tests, providers or engines.

## Review outcome and next action

**Historical signoff:** Claude's `review-2026-09-26T12-04-10Z.md` signs DESIGN
`baee80a35a9260ac9bd557aad8beb8fcb8ed44908b3f6e01e7f999fb22cfb1a8` and the
unchanged AGENTS/README digests above, resolves all first-review findings and
raises no further required change. Review SHA256
`31b4cf63702b5143219b8dc9942e842fec74c58c0db8a8355e5e22ffdef671ec`.
That review remains immutable historical evidence; it does not sign the new
DESIGN bytes. No product conformance or implementation acceptance follows.

**Complete:** Claude's new `review-2026-09-26T12-14-30Z.md` signs the amendment
and whole specification at the exact current DESIGN digest with no required
correction. Review SHA256
`265274512a0ee02d4980a98dee871eb05400aed044fb1513305a843ffb28d6d2`, 6750 bytes.
Prompt re-measured the three candidate documents and review after return; all
match. The review covers the amendment and affected surrounding sections, using
the prior review for unchanged material. Work is queued/unclaimed at the owner.

**Next owner decision:** align W270664 with the signed specification in a bounded
implementation handoff. Fix the three token failures and connect actual maintenance
execution, cessation and conditional return while completing the remaining F2
proofs. Pin exact ownership and explicitly identify any necessary wider scope.
The design is clear; implementation conformance and independent acceptance remain.
No W270664 execution was selected or resumed by this specification review.

Prompt owns the three documents plus FINDING/PLAN; the signed documents stay
unchanged. Claude owns its immutable reviews. No runtime tests, providers, engines,
deployment or Git mutations occurred. Human WIP checkpoint may include this final
review and updated FINDING/PLAN; a commit is not implementation acceptance.
