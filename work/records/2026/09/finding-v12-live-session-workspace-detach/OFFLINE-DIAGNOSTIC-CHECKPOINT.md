# Corrected offline diagnostics — W106673, claim 107407

M107404 schedules this bounded correction after the owner's failed offline run.
The original probe, six-artifact manifest, accepted reviews and retained runtime
artifacts remain intact. The actual runtime failure cause remains unknown.
This fixes the confirmed reporting defect; it does not change transport, image,
worker posture, credentials, namespace authority or success requirements.

Candidate: evidence/real_session_preflight_diagnostic.py.
Additive tests: evidence/test_real_session_diagnostics.py.
Review binding: evidence/real-session-diagnostic-manifest.json and the incremental
evidence/real-session-diagnostic.patch against the unchanged original probe.

After independent review and separate owner disposition, the exact proposed command is:

    /usr/bin/python3 /home/sl/src/baton/work/records/2026/09/finding-v12-live-session-workspace-detach/evidence/real_session_preflight_diagnostic.py --operator

Only the script basename changes from the reviewed operator command. Docker
create/stop arguments, image, user, flags, limits, clean environment and fixed
probe bind target remain identical. No blind rerun was performed by tuner.
The operator still needs the previously described local Docker execution
authority; this preparation adds no managed execution grant.

The inner probe records a fixed stage for identity, home preparation, version
command/check, help command/check, stream spawn/pinning, initialization send/read,
and idle continuity. Failures project a closed controller-authored reason code,
a numeric natural child exit status when observed, and numeric OS errno when
applicable. Unknown exceptions become unexpected-error. Exception text, filenames,
commands from exceptions, provider responses and provider stderr never enter the
diagnostic. Stderr remains DEVNULL; the fix does not transcribe it.

Examples distinguish identity refusal, missing executable, version mismatch,
missing required flag, command nonzero exit, malformed framing, correlation
mismatch, initialization refusal/timeout and premature CLI exit. Successful
version/help command status may be zero even when their subsequent content check
fails. Null child_exit_code means no natural exit status was observed at the
failure boundary, not successful execution. Cleanup-induced termination is not
reported as the original cause.

The host now accepts bounded stdout alongside Docker start's exit status even
when the status is nonzero. It parses the inside failure only through an exact
member set, fixed vocabulary and bounded numeric fields, then retains it in
result.probe. The host's own failure projection is result.failure;
result.docker_exit_code and the independently inspected container_exit_code remain
separate. A failure document still fails even when Docker reports exit0; a
success document cannot pass when Docker reports nonzero.

Cleanup failure is recorded separately and cannot replace a retained primary
inside failure. Failed container identity checks still refuse cleanup; stopped
resources remain retained for operator inspection. No diagnostic creates an
authorization or changes the failed-or-blocked outcome.

Read-only revalidation matched the original script against retained probe.py and
read result/registration from /tmp/baton-w106673-session-preflight-gu8vuv0e.
evidence/real-session-diagnostic-input-audit.json records those hashes and
observations. The owner's failure report and stopped state are historical input,
not a new runtime observation by this correction. No protected file was bypassed.

Verification: 11 new fault-path tests plus all four unchanged original local
tests pass. They cover both reporting boundaries, child nonzero exit, rejected
untrusted text/numeric fields, unknown exception and timeout redaction,
identity/version/flag refusal, malformed/control-correlation failures and cleanup
failure preservation. All runtime operations in the new tests are mocked.
AST comparison confirms the original local assertions, initialization guards,
container identity/posture checks, frozen inputs and exact create/stop calls
remain unchanged; the candidate adds reporting around those checks.

This checkpoint returns to baton.bug then baton.ops. It supersedes the previous
script only as the proposed next operator invocation after review; accepted
historical bytes remain where their manifest points. The owner-approved existing
automatic volatile credential delivery in M107362 remains resolved. Full live
session preparation resumes after exact-image transport evidence; real session/
restore/custody behavior, network identity and budget-cap disposition remain
separate pending checks.
