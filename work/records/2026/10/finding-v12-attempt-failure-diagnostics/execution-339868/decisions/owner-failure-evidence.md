# Native pilot failure evidence — 2026-10-19

Recorded by baton.prompt. This is an attributed evidence summary, not an independently executed review or a raw-output capture. Owner supplied the recovery/start/status, public diagnostic API, native-session tail and Docker-event outputs in the interactive conversation. Prompt independently read state/status.json, launch.json and manager/provider log tails from the retained instance. No store was opened with raw SQL. No tests, retry or deployment mutation were performed by prompt.

Instance: /home/sl/baton-instances/native-coordination-pilot-w321608-1
Host source: /home/sl/baton-builds/native-pilot-14e52d80
Authority: 1cdb8d19feda47c0a209bd0669b16871; native Work: 1cdb8d19-W1
Job: quickstart-a; submission: sub-w321608-quickstart-1; implementation episode1
Attempt: attempt-695f0b35db9f5a9419236e8c87352ea41ce8f3383f48fefcacf63b44f7da544e
Runtime: 8bad8ad99f920ce6d1b366dac0428178bf3c7e746422f91234ddd4ee23d03ed9
Launch operation: runtime.start:e0f18c6d970d959202a4a4a6fcffbf1c6160a7de6487433b8bb129d4304e6da4
Participant: baton.claude-pilot; assignment generation1

## Owner-observed timeline

- 15:01:58.140Z: recovery5 apply reports all four planned files applied and state_preserved=true.
- 15:01:58.307Z: recover reports abandoned=[] and recoverable=[], state_preserved=true.
- Start reports manager8283/publisher8284 and serving/publisher readiness. Subsequent canonical status observes one existing Job; no new submission.
- 15:02:47.793Z: attempt deadline reader reports started_at; deadline_at=null and policy=null.
- 15:02:47.795Z: workspace token acquired, domain workspace:66306:47749617, generation1, seconds900.
- 15:17:47.795Z: recorded token expiry, unchanged from acquired expiry. renewals=0, revision=0, renewed_at=null, renewals_remaining=4.
- 15:17:50.217Z: native transcript records successful Bash file-read result; no error/interruption in that last result. Last record is an attachment at15:17:50.218Z, not a completion or error.
- 15:17:51.772Z: manager's last activity observation, 594065 bytes.
- Docker event timeNano1792423071800349564: kill signal15 for the exact runtime; stop follows; die timeNano1792423071902937320, exitCode143 and execDuration903; destroy timeNano1792423071910379137.
- Token readback: same attempt/launch/runtime; expired=true, revoked=true, returned=true; expiry_judged_at=null, timing_ambiguous=false. Do not replace absent fields with guessed timestamps.

## Independently read by prompt, not an acceptance review

Canonical published status observed_at2026-10-19T16:02:24.637Z: implementation exceptional, runtime destroyed; exchange work dispatched with terminal=null; artifacts=null. Review blocked and has no runtime. Launch declares provider_turn_seconds3600 and verification_command_seconds900. Null artifacts does not prove the retained workspace contains no useful partial edits.

Manager log contains the old pre-recovery workspace-root refusal plus the successful current serving acknowledgement, without a new explanatory failure. Retained provider stderr has a no-stdin warning; stdout tail supplies no failure reason. Owner public attempt_start_failure_of and attempt_preparation_failure_of both return null. These absences are diagnostic limitations, not proof no failure occurred.

## Interpretation and remaining question

Confirmed observed mechanism: token expiry without renewal, revocation/return and exact runtime SIGTERM/destruction while the agent was producing activity. Runtime lasted903s rather than its declared3600s provider allowance. Source inspection identifies the host overdue-token reclaim path in tools/job_manager.py and tokens.py LIFETIME_SECONDS=900. The historical W275775 PLAN states production-consumer renewal migration was excluded. Revalidate the precise current serving wiring and bounded policy before changing code; token reader does not itself identify every reclaim caller or journal operation.

Authentication refresh and a separate later claude-default live-check failure are not evidence that authentication caused this termination. Preserve the original evidence and do not rerun to guess the cause. Normal Job detail currently says only exceptional/stage ended exceptionally; the owner selects a safe read-only diagnostic report and typed failure propagation to eliminate this investigation burden.

Retained source locations: state/status.json; state/manager.log; launch/implementation/<attempt>/launch.json and events/; launch/implementation/logs/<attempt>/provider.stdout.log and provider.stderr.log; native session file projects%2F-output%2F26d9ef71-c5c2-43e5-a2b7-4f40b0dbd1f3.jsonl. These are private diagnostic locators, not permission to publish transcript/credential content. Docker lifecycle evidence was obtained with bounded docker events filtered to the exact container; native/control state via public read-only owner APIs.
