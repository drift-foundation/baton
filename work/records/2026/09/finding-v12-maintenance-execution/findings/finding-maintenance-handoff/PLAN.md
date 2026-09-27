# Current owner selection — host initial preparation (2026-09-27)

The latest FINDING entry “owner selects host-side initial preparation” supersedes
the initial-preparation requirements and bootstrap decision in the checkpoint below.
Revalidate the ordinary host allocation/staging/input/permission path against
updated v12/DESIGN.md TOK-7 and HOST-1; no maintenance container is required for
initial preparation. Keep exclusive ownership, durable/revalidated handoff, sibling
isolation, no external I/O under DB locks, and refusal of launch/reuse while host
writers are unfinished or uncertain. Update H1–H9 and W285465 restart proof to
this model. Later cleanup/recovery/custody rules remain unchanged.

Existing serial path ownership remains. Preserve partial evidence and accepted
W285463; no child acceptance or graph change is implied. Routine continuation
returns to implementation, independent acceptance still required.

## Superseded checkpoint — historical context

# W285464 checkpoint — owner bootstrap decision

Claim286666; handoff286664/events286666; T285464 read through286584.
Review review-2026-09-27T15-24-51Z.md; exact candidate candidate-2026-09-27T15-24-51Z.json.
NOT ACCEPTED. Pass baton.decide for exact bootstrap mechanism/scope decision.

Confirmed: attempt-home bind excludes sibling attempts (probe PASS0.021s).
Blocked candidate operation: maintenance._cradled host os.mkdir(home,0700) before container
creation (probe FAIL0.010s). Current TOK-7 includes allocation; token/window does not exempt
host execution. Author one-mkdir expectation is not an approved behavior change.

Owner action: select compliant bootstrap approach/necessary bounded scope or explicitly
amend this exact requirement with lifecycle constraints. Reviewer recommends preserving
current isolation and governed-write placement. Author alternatives are not proven exhaustive;
no compliant-implementation impossibility claim. No new live run/deployment selected.

After disposition: author pins decision before product changes; complete _mounted/_prepared
ordinary no-context/no-review path, governed source/task/input staging/freeze/refusal cleanup,
then H1–H9 in advisory HANDOFF-PACKET.md and original FINDING. Claim-before-preparation,
exact cessation/settlement before conditional task admission, prepared identity revalidation,
replay without duplicate effect, unknown holds, actual mount and positive mutation/DB-lock
probes remain required. W285465 retains extra restart/integrated proof; graph unchanged.

Existing exact path ownership in FINDING remains; author PROGRESS/history preserved.
No candidate acceptance, child closure or broad migration. Human predecessor56431e14
inherited; this child has no accepted milestone. Preserve prior facility/G1 evidence,
R4 incident and unaccepted residuals. No agent Git, cleanup, live Docker/provider or deployment.
