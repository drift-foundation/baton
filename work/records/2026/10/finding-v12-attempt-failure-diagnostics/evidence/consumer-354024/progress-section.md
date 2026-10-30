
## 2026-10-22 — baton.claude, claim354024 — A CLOSED VOCABULARY IS CLOSED BY VALUE, NOT BY NAME

Successful canonical claim354024 after reading current state (queued,
unclaimed, routed `baton.impl`, `last_change_seq 354021`, zero open blockers),
the complete handoff through `work-events` (83 events, `next_after` null) and
thread T333486 in full (6 messages, `last_seq 353098`, unchanged). Read
`review-2026-10-22T18-28-00Z.md` and the reviewer's
`evidence/review-354007/` — `CANDIDATE.json`, `private-origin-input.json`,
`private-origin-output.json` and `packaged-proof.json`.

**The blocker is mine, it is real, and the worse half of it is a test I
wrote.** `_execution_limits` read boundary `origin` as plain `(str,)`, so an
arbitrary provenance string came back `known: true` with
`source: status.boundaries`. The producer owns exactly two origins — `job` and
`compatibility` — and never writes a sentence there. The reviewer's packaged
probe changed only `job-a/provider_turn.origin` to
`PRIVATE-CANARY-354007` in the previously product-composed status and the
binary echoed it verbatim.

And my own new case
`test_a_SECRET_nested_anywhere_in_the_limits_does_not_travel` **asserted the
canary travelled exactly once**, with a comment arguing that this was the
positive allowlist working because `origin` is an owned string member. It was
not. **An owned field NAME does not make every string in it an owned VALUE**,
and a test that blesses one leak is worse than the leak it blesses — it turns a
defect into an expectation. The reviewer is right that my acknowledging it in
prose did not make it accepted behaviour.

### The correction

- **`_closed(held, name, owned, source)`** asks the only other question worth
  asking about a closed vocabulary — is this one of the values its owner
  actually writes — after the type check. An unsupported value becomes a
  bounded unknown whose reason **names only what IS owned and never echoes
  what it saw**, because repeating the thing that should not have travelled is
  how it travels.
- Applied to **every** newly projected closed member, so the escape is not
  merely moved next door: boundary `origin` and `setting`, envelope `units`
  and `scope`.
- **And to `compatibility_generation`, which is one member beyond the four the
  review named.** An integer cannot carry text, but an unowned generation
  reported as known provenance is the same false claim. Stated here rather
  than slipped in.
- `seconds` and `default_seconds` stay **numeric** rather than enumerated: a
  ceiling is a number its owner bounds, not a vocabulary.
- `SOURCE_LIMIT_ORIGINS` and `SOURCE_LIMIT_GENERATIONS` are mirrored by value
  beside the existing name vocabularies, and the drift test now holds both
  against `execution_limits.JOB`/`COMPATIBILITY` and `GENERATIONS`.

**The prose correction.** `source_time_why` claimed a cause carries `at`;
`CAUSE_MEMBERS` emits no such member. It now names `source_observed_at`,
`execution.observed_at` and `execution.activity_at`, and says in terms that a
cause carries **no instant of its own** in this report. No cause timestamp was
invented and no producer capture was expanded, which is what the review asked
for.

### Verification

- **Focused: 42 tests OK** (was 39). Three new cases — every closed member
  rejected one at a time with no echo, both owned origins reported as known
  provenance across every boundary of both Jobs, and an unowned value not
  costing the valid facts beside it or the sibling Job. The corrected canary
  case now asserts **not one canary anywhere**, across `origin`, `setting`,
  `units`, `scope`, the generation, an unowned nested object and an unowned
  `requested` key.
- **Red before green:** the reviewed reader `b3932d12…` beside the corrected
  cases gives **42 tests, 7 failures and 9 errors** (`red3-arm.log`).
- **Joined 12-module gate: 1259 tests, 14.130s, OK, exit 0, zero skips.** The
  review permitted reusing the 1256 baseline; I reran it anyway and it is +3
  for the new cases.
- **Rebuilt command, both inputs the review named.** Bundle `5c8aa0af…`. The
  **original** input: exit 0, origin `compatibility` known, `provider_turn`
  3600, `observed_at` `2026-09-02T00:00:00.000Z` — nothing the previous
  correction established regressed. The **canary** input: exit 0, origin
  unknown with a non-echoing reason, `provider_turn` 3600 **retained**, and
  the canary string absent from the entire report.
- **Not rerun:** `tests.tools.test_packaging`. The review said no repeat
  packaging-version campaign, and the packaging provenance limitation keeps
  its prior classification.

### Candidate and cost

Changed by this claim, isolated root only:
`v12/python/tools/attempt_diagnostics.py` `b3932d12…` →
`6e02e22ef7ebd5cb4ae4725bc19a7c200b62897aba9f1f341435ceff2bb4fd12` and
`v12/python/tests/tools/test_attempt_diagnostics.py` `faea822a…` →
`3882768c6c8a482c6a2df5b15552b1beef2c585a2c6ef3589127f300a9d75cca`. The
accepted child producer is untouched and every other consumer file is
byte-unchanged. Evidence with digests in
`evidence/consumer-354024/INDEX.json`
(`acacb4b8edb83ee509112eac5fff32e9575607876fef14b3cf6c636d1dc0ce70`).

No producer relaxation, no expanded capture, no shared import or edit, no Git
mutation, no live provider or engine, no deployment, no installed-root edit, no
recovery, no new split. W339626 untouched. Measured this claim: focused 0.105s,
red arm 0.135s, joined gate 14.130s once, one bundle build ≈5.9s, two packaged
invocations ≈0.3s each, plus unmeasured reading. Prior parent ≈2253s and child
≈5726.14s plus unknowns stay separately attributed.
