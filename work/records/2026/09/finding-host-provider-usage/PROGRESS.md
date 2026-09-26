# W266071 implementation — baton.tuner, 2026-09-25

Claim266170; binding266181. Ready for independent review, then owner.

Implemented one bounded Codex account read after the preserved login/live checks.
Validated duration mapping, remaining percentage, UTC resets/local observation,
unknown reasons and separate credits wording. Claude allowance remains explicitly
unsupported/unknown: no supported noninteractive source established. Docs explain
limits, subprocess counts, informational usage status and existing exit codes.
The existing just recipe and unrelated shared-tree changes were not modified.

Verification: `python3 -B -W error::ResourceWarning -m unittest discover -s tools -p test_provider_checks.py -v`
passed all 13 tests, unittest measured 4.365 seconds. This is the only current
Work test run; cumulative author verification 4.365 seconds. Final follow-up
changed only credits wording and documentation. `git diff --check` passed;
product paths are untracked inherited additions from W265097, so that command
alone does not inspect their contents. New tests run fake CLIs only, including
the real just entry point, strict RPC sequencing, per-home environment isolation,
malformed/error/overflow/early-exit responses, timeout descendant cleanup, window
validation, stale resets, unknown sources and unchanged aggregate verdicts.
No real provider query, live model, auth mutation or v12 operation was run.

Changed existing test expectations only for the additional Codex usage process
(counts and Claude call index); preserved all original login/live coverage.
Added three usage-focused tests under the standing test authority. Independent
review should assess app-server source semantics, safe unknown handling and
isolation; fake coverage does not establish live provider availability.

Review these final filesystem bytes:

- `tools/provider_checks.py` SHA-256 `ad8ac83f622831b757ba6c46e80719dd5ef32879ceebadfebed12b9e448b5d7a`
- `tools/test_provider_checks.py` SHA-256 `589d7ddcd905c5d9aa9da895fcf86f26163af83259f2e5a594cee51c3f0a99c1`
- `docs/PROVIDER-CHECKS.md` SHA-256 `f1698fb5de17ca54b2ee099340b36dca1406a6091add2e8762b3458b5dbdb251`

Owning decision and current plan: FINDING.md and PLAN.md in this dossier.
After independent acceptance, owner confirmation command remains
`just provider-checks` with the existing optional private configuration argument.
Do not run that command against real providers during author/reviewer checks.
Git/index/history remain owner-owned.

## 2026-09-25 — owner presentation correction, tuner claim266245

Applied owner reroute266241 and latest FINDING ruling. No independent review
had occurred before this reroute. Revalidated existing structured fields and
kept their validation/query/exit semantics. Output groups each account under
one label, combines login/live status, shows readable UTC resets and one local
observation time, and collapses wholly unavailable usage into one explanation.
Partial windows receive concise missing-data notes. Raw source/window fields,
repeated unknown fields and credit notices are removed from normal output;
docs retain the distinction between credits and subscription allowance.

Updated rendering assertions in tools/test_provider_checks.py and added partial,
missing, stale and missing-reset presentation coverage. All prior semantic,
isolation and cleanup tests remain. The focused fake suite passed 14 tests in
4.366 seconds; cumulative W266071 author verification is 8.731 seconds.
No live provider calls. git diff --check passed (untracked product paths remain
outside its coverage). Documentation includes an illustrative compact report.

This candidate supersedes the earlier candidate hashes for review:

- `tools/provider_checks.py` SHA-256 `c7e2b264108ece18058edb1565bdf633747a024fdf94502c997a74652c0bc9e3`
- `tools/test_provider_checks.py` SHA-256 `b6165859afe80a0b1862a9061428d3985dadb6adc5cf65f269a5576e74c75431`
- `docs/PROVIDER-CHECKS.md` SHA-256 `73b997a29a7ec3cc7c1fe0f46922ffc07ce54f9d3a6545af1828fd0398acda35`

Ready for independent review via baton.bug, then owner.
