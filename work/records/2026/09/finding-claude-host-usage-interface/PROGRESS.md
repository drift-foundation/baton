# Partial Claude usage collector — baton.tuner, 2026-09-25

Owner266417; claim266419. Ready for independent implementation review.
Latest prior review review-2026-09-25T13-56-58Z.md accepted investigation only.
Implementation decision is pinned in FINDING.md; source-backed design remains
RECOMMENDATION.md (unchanged). PLAN.md carries current review state.

Claude live argv now uses stream-json plus verbose, keeping the same isolation
flags and one ping. Unique terminal result determines its existing verdict.
Public rate_limit_event data is mapped to session/week only with matching
nonempty terminal session identity. Explicitly conflicting stream identities,
missing attribution, invalid fields, stale resets and conflicting same-window
samples cannot manufacture quota. Identical repeated samples are accepted.
Unknown/model/overage types and internal unifiedWindows are ignored. Existing
bounded process runner, Codex query, account selection and aggregate exit remain.
Quota from valid attributed failed terminal results can remain informational;
it never changes that failure to success. Timeout/truncated output yields none.

Changed paths: tools/provider_checks.py, tools/test_provider_checks.py,
docs/PROVIDER-CHECKS.md and this dossier only. justfile unchanged. No v12,
experimental request, report fallback, credential inspection or live calls.
Existing tests updated for stream format and missing-window wording; added
subprocess-level no-extra-call check and sparse parser/attribution cases under
standing test authority. All login/live and process cleanup regressions retained.

Focused command:
`python3 -B -W error::ResourceWarning -m unittest discover -s tools -p test_provider_checks.py -v`

First run:16 tests, one assertion failure in4.637s: ordinary floating-point
representation of42 differed by~1e-14. Changed that numeric expectation to
assertAlmostEqual, without altering percentage logic or weakening behavior.
Second run:16 tests passed in4.550s. Cumulative W266297 author verification9.187s;
prior investigation/reviewer ran no tests. Documentation-only example wording
followed passing run. No broader tests or live verification needed in this scope.

Final candidate:

- `tools/provider_checks.py` SHA-256 `bf9b3871a704953528712a2e87040d290bb17f73d5707cf77e430d58ff3fa2d3`
- `tools/test_provider_checks.py` SHA-256 `97c815e19bebec157614fdfa62faeadd8700255627f4c269116764a886bee32a`
- `docs/PROVIDER-CHECKS.md` SHA-256 `8a4d18312b35fea694316d9cf47c536692f3bc466e2d64089fbc00e0cb6f4952`

Independent review then owner. Owner confirmation after acceptance remains
`just provider-checks` with the existing private account inventory. Partial
stream coverage cannot guarantee both windows; manual selected-account /usage
remains documented human fallback. No author live acceptance claimed.

## R1 correction — baton.claude, claim 266470

Review 2026-09-25T14-07-55Z asked for one bounded correction, and it was exactly
right. In `classify()`, the Claude live branch answered `failure(err, code)` when
`claude_events` found no unique terminal result — so the provider's structured
diagnostic on STDOUT was thrown away and a recognized failure came back
`failed (unclassified; exit=1; ...)`. The same branch serves conflicting result
streams, so those lost their diagnostic too.

THE FIX IS ONE OPERAND: `failure(out + err, code)`. It changes nothing about
success, which still requires exit 0, a unique terminal result, `subtype
success`, `is_error false` and a non-empty string result; and it discloses
nothing, because `failure` answers fixed sanitized text. The Codex branch already
passed `out + err`, which is why only Codex ever exercised the fake's `quota`
mode.

THE DOCS NEEDED NO CHANGE, and that is the point: `docs/PROVIDER-CHECKS.md`
already promised that recognized quota/rate-limit and authentication diagnostics
are distinguished and that raw output is never printed. The documentation was
right and the code was not delivering it on this one branch.

TWO REGRESSIONS, both failing before the fix:

- `test_an_unsuccessful_stream_without_a_terminal_result_is_still_classified` —
  in-memory over `classify` directly: a structured stdout error classifies as
  `usage-limited` and `authentication-error`; a stderr-only diagnostic still
  classifies; an UNKNOWN diagnostic stays unclassified and none of its words
  appear in the answer; a zero exit with no unique terminal result stays
  `inconclusive` so quota can never manufacture success; and conflicting terminal
  results stay unsuccessful while still being classified.
- `test_a_claude_quota_stream_is_classified_through_the_fake_cli` — the same
  correction end to end through the existing fake `quota` mode, asserting
  `usage-limited` appears, `login: ok` is unaffected, and `DO-NOT-PRINT` appears
  nowhere.

NON-VACUITY, MEASURED. With the single operand reverted in place, both new cases
fail with exactly the string the review predicted —
`'failed (unclassified; exit=1; ...)' != 'usage-limited'` and the same text in
the end-to-end stdout — and the file was restored in the same act, verified by
re-hashing.

VERIFICATION. `python3 -B -W error::ResourceWarning -m unittest discover -s tools
-p test_provider_checks.py`: 18 tests passed in 4.481s (16 before, plus these
two). The revert probe ran 2 tests in 0.043s, deliberately red. No live call, no
credential or transcript read, no provider contact, no v12 scope. Cumulative
W266297 author verification: 9.187s prior + 4.481s + 0.043s = 13.711s.

Candidate after R1:

- `tools/provider_checks.py` SHA-256 `1e7cfcae974a609c99c9c5263ea5cb871674ad7b8fd3978b2730e3792425aaf9`
- `tools/test_provider_checks.py` SHA-256 `fa1a2ca282877a6e5a5ab31eb28db72c5d5a89da38834a4944dcbdabbb0d2ccc`
- `docs/PROVIDER-CHECKS.md` SHA-256 `8a4d18312b35fea694316d9cf47c536692f3bc466e2d64089fbc00e0cb6f4952` (UNCHANGED)

Independent re-review next. Owner confirmation after acceptance remains
`just provider-checks`; nothing about the partial-window limitation changed.

## 2026-09-25 — final timestamp and usable rows, tuner claim266562

Applied owner266554, already pinned in FINDING/PLAN, after reading accepted R1
handoff/review-2026-09-25T14-17-41Z.md. Revalidated current rendering: it still
printed per-account Observed, unavailable and reset-only rows. Changed only
render_usage and the final main report timestamp in the helper. Per-sample
observation/stale validation, parsing, source selection, process boundaries and
R1 sanitized stdout classification remain unchanged. Final timestamp labels local
report completion, not simultaneous measurement. No usable allowance means only
login/live for the account. Valid zero remaining still prints; missing reset on
otherwise usable allowance still prints reset not reported.

Updated existing rendering expectations in tools/test_provider_checks.py for
latest owner behavior, including mixed/all-unavailable, reset-only, stale rows,
once-only final timestamp and unchanged login/live diagnostics. Preserved R1
regressions and internal quota validation. Docs reflect final presentation.
Owned paths helper/tests/docs plus dossier; no other files changed by this claim.

Focused fake suite:18 tests passed in4.901s, same documented unittest command.
No live calls. Author total18.612s; measured Work total28.439s including prior
reviewer9.827s, plus historical tiny unmeasured reviewer probes. No further tests
needed for this rendering-only change. Final candidate supersedes prior hashes:

- `tools/provider_checks.py` SHA-256 `37fce0bacc8998a81204414066287ca2b81e47d5f4e8f32a7c43bf52e315f986`
- `tools/test_provider_checks.py` SHA-256 `2f60876547bdf11ecfcc7f6e84b197de766c3a2420bf8698c4037c6755336568`
- `docs/PROVIDER-CHECKS.md` SHA-256 `2e17f23c2d76f045a41eb7df5268826c8edf0b9121507ea01f265c01c5c7d66a`

Ready for independent review then owner. Git state remains owner-owned.
