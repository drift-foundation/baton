# Plan

1. Done: create W114322 and pin owner-approved scope and deduplication rules.
2. Done: add incident/runtime reads and correlated advisory detection.
3. Done: 28 focused tests pass; candidate/delta inspection complete.
4. Independent review found a stale-lease deduplication defect; see
   `review-2026-09-07T23-44-02Z.md`. The reported 28 passing tests do not cover it.
5. Done, 2026-09-08: the foreground change author preserves accepted runtime
   failure versions and pairing acknowledgements across derived `unknown` from
   lease expiry, within the existing three-file scope. Add regressions for an
   accepted failure expiring and renewing unchanged, including paired attention;
   retain coverage for rejected attention and real recovery followed by a new
   failure. Update notifier documentation if necessary. Run the focused notifier
   module only, expected under 10 seconds, and retain the revised candidate and
   verification evidence for independent review. Evidence is retained under
   evidence/correction-2026-09-08/: exact three-file candidate, baseline deltas,
   SHA-256 manifest, unchanged-existing-test AST audit and 36-test passing output.
6. Done: review-2026-09-08T01-02-34Z.md independently signs off the revised
   candidate, including expiry while unrelated attention is accepted and runtime
   pairing across incident dismissal. Exact bytes, baseline/test preservation and
   retained passing transcript are in evidence/review-114925/.
7. Current: operator restarts only the existing notifier at the signed-off bytes,
   preserving config, cursor and prompt targeting, and supplies the requested
   visible proof before closure. Source sign-off alone is not live delivery proof.

This is one bounded correction to the same notification behavior, with the same
author and file boundary; it does not need a separate implementation Work.

Foreground change author: baton.prompt. No managed claim or readiness consumed.
