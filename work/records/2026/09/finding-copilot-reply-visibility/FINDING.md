# Copilot advice generated but not visible to the operator

Work W119521. Recorded 2026-09-08 by baton.prompt, read-only diagnosis.

## Observed

Slawomir reported that copilot had not brought obligation119430 to his
attention. It was still pending when checked, and he subsequently ran the two
recommended commands. Snapshot119493 confirms it is no longer pending and
W71879 has the requested W119400 prerequisite. The other pending obligation
at that snapshot belonged to tuner, not Slawomir.

## Confirmed delivery trace

- Obligation119430 created on T115599 at13:22:58UTC.
- Dispatcher accepted operator-attention at13:22:59.723UTC and started turn
  `01a0812f-aa0c-7e82-b342-99ed226e8385` at13:22:59.727UTC.
- The configured prompt thread is `01a08124-bd0e-7271-aa3c-e0fd5846a8cf`.
- Its rollout records the advisory input, commentary at13:23:03.279UTC, and
  the full recommendation plus exact block/respond commands at13:23:55.733UTC.
- Dispatcher records successful turn completion at13:23:55.808UTC.
- A separate read-only app-server connection to ws://127.0.0.1:4500 performed
  initialize and thread/read(includeTurns=true), without resume/start/subscription.
  It returned the same completed turn and final_answer agentMessage
  `msg_000143d54051bc60016aa00c62508487d2bfc73851d1f20c2e`, beginning
  "Obligation 119430 is still pending", with both owner commands intact.

Locators: deployment log `log/codex-dispatcher.log` beneath
/home/sl/baton-v11.14aecfb, and
/home/sl/.codex/sessions/2026/09/08/rollout-2026-09-08T07-11-03-01a08124-bd0e-7271-aa3c-e0fd5846a8cf.jsonl.
No store or raw SQLite inspection was used.

## Confirmed limitation, distinct from suspected defect

tools/codex_copilot_notifier.py poll() advances its local seen hashes on the
bridge's accepted response. That proves admission, not model completion or UI
receipt. The documented contract explicitly makes the same distinction. An
unchanged unanswered obligation therefore does not automatically produce another
advisory. This behavior does not explain a persisted answer's visibility by
itself and is not evidence of a failed notifier poll in this case.

The bridge's client subscribes to the configured thread and receives completion;
it does not implement the operator client's rendering. Official app-server docs
distinguish thread/read (stored data, no subscription) from start/resume event
streams and describe per-connection notification opt-outs. Those are diagnostic
boundaries, not proof of the operator client's behavior:
https://learn.chatgpt.com/docs/app-server

## Open

Actual operator client, endpoint/thread selection, subscription/reconnect
history, and receipt/rendering of this final-answer item have not been observed.
The response is absent from the conversation history presented in this copilot
context; that alone does not establish what the physical UI received.
Suspected boundary is between stored/thread-readable output and client display.
Do not label this a confirmed OpenAI defect or a confirmed frontend omission.

No replay, cursor reset, new model turn, implementation, tests or restart was
performed. The earlier emergency claim exception applied only to W119195.

## 2026-09-08 — Operator clarification and proposed reminders

Slawomir clarified that he may have missed the recommendation and asked whether
unresolved obligations could remind again after 5–10 minutes. This supersedes
any interpretation of the original report as confirmed missing UI delivery;
the transport/display defect remains unproven. Obligation119531 was still pending
at snapshot119573. Its notifier turn began at13:36:09UTC and the rollout retained
the recommendation at13:36:44UTC. Baton title boldness includes unresolved
personal obligations and does not indicate whether an advisory was delivered.

Proposed behavior, not yet implementation authority: a configurable ten-minute
reminder interval for the operator's still-pending response obligations. Retain
each obligation's hash plus its last accepted advisory time and reminder
generation; expiry makes that obligation eligible again without clearing the
whole cursor. Re-read canonical obligations before sending, prune resolved or
no-longer-owed entries, coalesce due reminders, and preserve idle-only admission.
Busy/rejected delivery must not advance the timer. Unrelated accepted attention
must not postpone an obligation's reminder. New or changed obligations remain
immediate; other attention categories retain current change-based deduplication.

Reminder generations must distinguish successive accepted reminders in event
identity while retries of the same generation remain stable. Old hash-only
cursors need a documented migration, and deterministic clock-controlled tests
must cover expiry, resolution, busy/rejection, unrelated deliveries and restart.
Proposed configuration name: obligation_reminder_seconds, default600, with0
disabling reminders. This requires notifier code/tests/documentation changes;
the current config parser does not accept that setting. No runtime setting,
cursor, implementation or process was changed by this discussion.

## 2026-09-08 — Managed verification interrupted

The approved reminder candidate was written under tuner claim119728, but its
verification/handoff was interrupted by an execution-permission failure and
managed approval quarantine. See FAILURE-119728.md for exact evidence and
recovery recommendation. Twelve new controls pass; the full module reports
47 passing tests and one Unix-socket permission error. No completed reminder
deployment or independent acceptance is claimed.

## 2026-09-08 — approved reminder implementation, claim119728

Slawomir's reroute event119722 approves the reminder contract above and assigns
tools/codex_copilot_notifier.py, additive tests in
tools/test_codex_copilot_notifier.py and tools/CODEX-COPILOT-NOTIFIER.md to tuner.
This supersedes the proposed/not-yet-authorized reminder status. Default600,
configurable300, and0 disables; keep Normal priority and return to baton.bug
for independent review. No automatic live restart is authorized or planned.

Revalidated current code: poll stores hashes on bridge acceptance, its event
identity has no reminder generation, and read_config refuses the new setting.
Implement optional per-response-obligation records containing the accepted
hash, wall-clock acceptance timestamp and accepted generation. New/changed
obligations stay immediate; unchanged pending response obligations become due
at the configured interval. Trials and all other categories keep change-based
deduplication. Each poll reads the canonical obligation set and exact current
handler membership before offering any event.

Old hash-only entries have no recoverable acceptance time: retain their hash,
record a one-time migration anchor and generation0, and allow the first reminder
one interval after that anchor. Keep acceptance time null until a corresponding
event is accepted. Migration alone never claims a new delivery. Persist this
anchor even while busy so restart or unrelated advice cannot defer it forever.
Scope changes retain the existing fresh-attention semantics. Resolution or lost
handler membership prunes reminder records.0 disables expiry, preserving hashes
and accepted timing for later re-enablement.

An event carries at most50 exact locators. A successful send must acknowledge
only those offered locators (plus the existing paired failure representation),
not every item from the scan; otherwise an omitted obligation would falsely
acquire an accepted timer. Later polls offer the remainder. Generation identity
is stable while a given reminder remains unaccepted and changes after acceptance;
the clock is not part of event identity. Retain the existing admission checks,
failure pairing, stale-runtime memory and authority/thread/bridge scope.

## 2026-09-08 — reviewer evidence-access finding, claim119798

Owner event119796 reports the missing socket control passed and names
`/tmp/w119521-socket-test.txt`, asking the reviewer to retain it in this dossier.
Reading that exact file returned `No such file or directory` in the managed
reviewer context. The reported pass is not disputed, but the required output
cannot yet be inspected or retained. Publish that result under this record's
shared `evidence/` path, with the exact command and candidate hashes if available.
This may reflect temporary-path visibility/lifecycle; no cause is established.

The reviewer will reuse the existing 47 passing results and independently audit
the preserved candidate while that evidence is supplied. No socket re-execution,
escalation, process restart, deployment or acceptance without the missing result
is authorized by this observation. The earlier managed failure/quarantine
history remains intact.

## 2026-09-08 — confirmed candidate batching defect, claim119798

**Confirmed.** The approved reminder candidate can starve pending attention:
with60 obligations and supported300-second reminder/poll intervals, each
successful due poll offers the same lexicographically first50 keys. The other10
never receive their first advisory; if all60 were initially accepted, those10
never receive a due reminder instead. Exact two-scenario reproduction and
candidate hashes are in `evidence/review-119798-starvation.json`, generated by
`evidence/reproduce-reminder-starvation.py` without live tools or sockets.

`review-2026-09-08T14-17-52Z.md` requests a bounded fair selection order and
additive controls within the approved three paths. This supersedes any reading
of the documented "later polls offer the remainder" as verified candidate
behavior. The intended reminder contract itself is unchanged. Source review
retains47 prior passing controls; M119806 still requests the separately
reported operator socket result at a readable dossier path. Work remains open
for correction, eligible execution placement and independent re-review.

## 2026-09-08 — batching defect corrected, claim119876

**Confirmed corrected.** The starvation `review-2026-09-08T14-17-52Z.md` measured
is fixed at `tools/codex_copilot_notifier.py`
`112e00ecf69bb2a0fae2bf02cfb257e14508435daf4c766b498fd19103f631d9`, with additive
controls at `tools/test_codex_copilot_notifier.py`
`618bc9900d1ed345fdfc27b607525ab4abc2fc40dee9f81c742bf3728e481993` and the
ordering contract documented at `tools/CODEX-COPILOT-NOTIFIER.md`
`c636f56d217a1e1b46d18dba2ad640a8e3e8026711267e71499ecb4ad82ec573`. The reviewed
candidate hashes were revalidated against the tree and the reviewer's own probe
re-run before any edit; both scenarios reproduced exactly. This explicitly
supersedes the key-ordered batch as current candidate behaviour, and the
reviewer's measurement remains valid evidence about the superseded ordering.

`poll` orders the batch by PRIORITY rather than by locator: genuinely new or
changed attention first, then due reminders keyed by each record's own anchor —
its acceptance time, or the migration anchor of a legacy entry — oldest first
with the locator breaking ties. Acceptance moves a record to the back, so the
longest-waiting obligations lead the next eligible advisory. The fifty-locator
bound, event identity for retries of the same pending batch, generation
advancement only for accepted offered locators, legacy migration, failure
pairing and busy/refused semantics are unchanged, and no existing assertion was
altered.

Measured: `evidence/correction-119876-drain.json` shows both reproduced
scenarios draining — all sixty obligations advised, nothing permanently omitted,
each batch still exactly fifty. Four of the five new controls fail when only the
ordering line is reverted; the fifth is a preservation control for retry
identity and is named as such rather than counted as a regression. The whole
module is 53 tests OK, retained at `evidence/regression-119876.txt`.

**Socket control, and the distinction event119869 requires.** The module's
Unix-socket test PASSES in this managed context, inside that retained 53-test
run against the corrected hashes — an independently inspectable artifact at a
shared dossier path, which M119806 asked for. It is NOT the operator-side result
event119869 requires before acceptance: that is an operator-context act, it was
not attempted, and this run is not offered as a substitute. It establishes only
that the correction introduced no socket failure and that the control is
exercisable. The earlier EPERM in the quarantined tuner context stands as
recorded; the difference is environmental and no cause is diagnosed.

The original UI visibility question is untouched and still unproven; no cursor,
notification, deployment or process was changed. Independent re-review of this
correction remains required before this Work closes.

## Independent re-review — 2026-09-08, claim119916

The starvation correction is independently verified for the three exact hashes
in `review-2026-09-08T14-34-09Z.md`. Five new controls and a separate mixed
incident/runtime-pair probe pass. All 48 earlier tests are byte-preserved;
only ordering and anchor bookkeeping differ from the previous source candidate.
The retained 53-test author result is read and reused. This supersedes the
pending correction/re-review state, but not the acceptance gate: M119869 still
requires a fresh operator-side socket result against this candidate, saved
inside the dossier. The managed implementer pass is not a substitute. Return
to baton.ops to supply that artifact and then baton.bug to inspect it.

**Diagnostic supersession.** `DELIVERY-119806.md`, section Confirmed attachment
mismatch, records prompt-owned host and rollout evidence that the human's Codex
CLI was attached to the old thread while automated advice went to the configured
new prompt thread at the same server. This supersedes earlier statements that
the client/attachment are still unidentified and the corresponding portions of
the implementation account. The backend-versus-display caveat remains valid:
no rendering/transport defect is established. Actual reattachment and visible
recovery are not asserted; reminders do not correct the thread mismatch.

## Final acceptance — 2026-09-08, claim120004

Owner handoff119986 supplies the fresh operator-side socket result directly at
`evidence/operator-socket-test.txt`. Independent inspection confirms one test OK
and all three tested hashes match the current candidate and prior independent
review. `review-2026-09-08T14-46-00Z.md` accepts the bounded reminder candidate;
`evidence/review-120004-acceptance.json` binds the artifact and source hashes.
This supersedes the pending operator-evidence/acceptance state; historical
missing-file and quarantine records remain intact. No further test run or
application edit was required. Close W119521 satisfying for diagnosis and the
approved reminder change. Deployment, notifier restart, client reattachment and
visible recovery are not asserted by this acceptance.
