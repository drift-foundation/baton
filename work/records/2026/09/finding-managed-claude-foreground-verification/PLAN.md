# Plan

1. Done: record failure mechanism, supported setting and operator decision.
2. Done: prepare exact one-key template change, preserve baseline and verify
   that all unrelated JSON values remain equal. Operator applied the setting;
   post-restart reads confirm value "1" in template and generated context.
3. Done: return W110935 and W114085 to Claude within their existing bounded scopes.
   Keep their existing independent review and test-evidence requirements.
4. Done: operator restarted the configured service set from an external terminal;
   all nine services report healthy and the new Claude bridge PID is 2425531.
   Operator subsequently resumed dispatch.
5. Done: Claude collected a reported 371-test result (29.088 seconds, OK) and
   returned W110935 normally at event114825; codex claimed review at114828.
   The canonical event evidence and explicit evidence limits are recorded below
   in FINDING/PROGRESS and evidence/foreground-work-events.json.
6. Current: operator terminal close as satisfying, authorized in the interactive
   approval. baton.prompt has no close transition for this baton.ops Work.
   Revisit adapter/bridge behavior if the same failure recurs; product review
   of W110935 and W114085 continues under their own acceptance requirements.
