# ACP managed turn ends while its Work claim remains held

Work W133361, created with canonical binding133361 in response to owner
poke133350. Reviewer baton.codex/rview investigates incidents47/48/49 on
W133117 and owner instruction M133314. This runner lifecycle finding is separate
from the active integration-result implementation and its verification budget.

## Initial observations and scope

Canonical snapshot133353: W133117 is held by baton.claude, claim133353,
ACP session575dbde0-cb82-423a-9c06-8d76ab073eee reported working. Do not steal
the claim, interrupt the process, change implementation files or run P tests.
No workaround or protocol/application change is authorized by this research.

Questions: what ended each turn; whether M133314 was delivered/read; whether
an agent chose to finish or a runtime/provider limit interrupted it; and which
owner boundary needs correction. Findings must separate observed, confirmed,
inferred and unavailable evidence. Use canonical CLI for coordination state,
never read its database directly. Retain only relevant sanitized runtime facts.

## 2026-09-10 — independent investigation of incidents47/48/49

**Confirmed:** all three recorded assistant finals have `stop_reason: end_turn`.
They explicitly say the claim is still held and list unfinished implementation.
This is evidence of normal agent turn completion, not a timeout or token-limit
termination. The observed behavior contradicts the repository requirement to
pass or close claimed Work before ending. Progress notes do not release custody.

| Incident | Readiness episode | Claim | Assistant final UTC | Incident UTC | Owner recovery |
| --- | --- | --- | --- | --- | --- |
| 47 | 133208 | 133218 | 03:47:46.720 | 03:47:47 | release133270 at03:50:43 |
| 48 | 133270 | 133275 | 03:54:12.162 | 03:54:12 | release133315 at03:56:37 |
| 49 | 133315 | 133318 | 04:01:14.172 | 04:01:14 | release133349 at04:02:46 |

All dates above are 2026-09-10. Canonical Work events and incidents corroborate
the same session575dbde0-cb82-423a-9c06-8d76ab073eee and current runtime
incarnation5e452a23-257a-4501-af34-1da08ab42149. Prompt timestamps are
03:41:02.168, 03:50:47.069,
and03:56:41.024; turn durations are approximately405,205,273 seconds. Neither
the configured7200000ms/two-hour deadline nor a fixed short timeout explains
these endings. Do not use the rounded durations as verification-budget charges.

The second final gives unusually direct behavioral evidence: "each increment
now ends with a durable record, so an orphaned claim costs a redelivery and
nothing more." It describes recovery as an accepted work cadence. The third
final again says "I hold claim 133318" and reports remaining work. There is no
pass/release/close attempt in these three turns. These are public final-response
excerpts, not private reasoning.

### Did M133314 reach the third turn?

**Confirmed:** Slawomir posted M133314 to T133117 at03:56:37, before release133315
and the third prompt at03:56:41.024. It explicitly says recovery is exceptional,
requires continued work within the live turn, and requires incomplete work to
return through baton.bug before ending, with partial work and budget preserved.

**Confirmed from the recorded inputs:** the instruction was not presented in
that turn's public prompt, tool results, or file attachments. The readiness
prompt contains only Work identity, role instructions and launcher contract.
Claude called `detail` but piped it through a Python filter printing only
phase/handler/claimed_at/pickup/ready. The exact result at transcript line1594
is five scalar fields; no thread locator or message body survives. It then
claimed and proceeded with source work. It never called `thread` for T133117.
The full inspected window contains zero matches for M133314, its distinguishing
text, or its incident47/48 prefix in public messages and attachments.

This is **not evidence of knowingly rejecting M133314**. The instruction was
durable in Baton discussion but was not consumed by this turn. Installed
`baton_readiness.mjs:25-48` deliberately emits compact Work prompts without
discussion bodies. Plain discussion does not itself create a readiness action
(`docs/AGENTS-MAILBOX-PROTO.md`). The model's filtered read and omitted thread
read are the immediate consumption gap; the bridge did not promise to inject
the discussion text. Treating a plain post followed by redelivery as proof of
instruction delivery would be an operational error.

### Runtime boundary and evidence limits

**Observed installed deployment:** bridge PID3651854 executes the0650c61
installed source with explicit claude-acp.json. That config names adapter0.69.0,
sets `turnTimeoutMs=7200000`, and retains
`CLAUDE_CODE_DISABLE_BACKGROUND_TASKS=1`. The earlier W114716 foreground-task
setting is present; this finding does not propose repeating its restart.

**Confirmed source behavior:** AgentSession races prompt completion against
process death and the configured deadline. The bridge awaits `promptText`,
discards the returned response, settles the process domain, and checks canonical
claim custody. The held-claim incident is a custody diagnostic, not the provider
stop reason. Installed adapter code separately handles max_tokens, budget and
max-turn errors; however, no raw ACP response or SDK terminal-result packet is
retained here. The positive `end_turn` evidence comes from the actual assistant
message records and agrees with their complete final text and incident timing.

**Operational evidence limitation:** `readlink /proc/3651854/fd/1
/proc/3651854/fd/2` returned exit1 with no locator, so bridge stdout/stderr was
not inspected. No escalation or process intervention was attempted. An initial
guessed adapter package directory was absent; resolving the configured executable
located the actual @agentclientprotocol package, whose source was then read.
No required repository policy/dossier was left unread. We cannot exclude an
unrecorded trailing SDK event, but the evidence does not support calling any of
these three terminations a runtime limit, crash or background-test interruption.

### Proposed correction boundary — requires owner disposition

1. Tighten the managed implementer turn contract so each readiness turn claims,
   reads the complete current handoff and associated Work discussion, and
   continues until an explicit handoff or incomplete-work return. A final
   response while holding a claim is forbidden even after durable progress.
   The mailbox guide's weaker "neither progressed nor handed back" wording can
   be misread as allowing progress-only endings; AGENTS.md already requires
   pass/close. Clarify that discrepancy in a separately authorized policy scope.
2. Deliver the correction through an input path that actually reaches the
   managed turn, with a thread-read requirement, rather than assuming another
   plain post plus owner recovery constitutes delivery. Do not interrupt the
   current implementation as an incidental research action.
3. If runtime observability is separately scheduled, preserve the returned ACP
   stopReason with action/session correlation in runner evidence. This would
   avoid reconstructing future causes from local transcripts. Preserve the
   existing fail-closed claim fence and process cleanup; no automatic release,
   continuation loop, timeout extension or budget increase is justified here.

Acceptance for a selected behavioral correction: observe one corrected turn
receiving/reading the actual instruction and reaching a canonical pass/return
before its final response, with existing partial implementation and cumulative
verification spending carried forward. This is a proposal, not a completed fix.
No additional product verification was run for this investigation.

### Evidence and preservation

- `evidence/incidents-47-49.json`: canonical incident snapshot133363.
- `evidence/work-thread.json`: exact M133314 and original instruction,
  canonical snapshot133393.
- `evidence/work-events.json`: claims and owner recoveries, snapshot133393.
- `evidence/transcript-extract.json`: selected public prompts, finals and Baton
  command inputs with source line locators; no private reasoning retained.
- `evidence/transcript-validation.json`: per-line SHA256 for the200 timestamped
  source records inspected, public-content search results, stop-reason counts,
  attachment metadata and exact third-turn filtered detail result.
- `evidence/runtime-source.json`: installed source excerpts with full-file
  digests, selected config facts and unavailable log-locator observation.

Only this operational dossier and its evidence were written. W133117's claim,
implementation, runtime, progress and budget were not mutated by this reviewer.
At snapshot133393 W133117 still held claim133353; this investigation owns only
W133361 claim133363. Existing implementation claims of0.45s,1.11s and2.12s in
the three finals are preserved as author statements, not re-audited or reset.

## 2026-09-10T04:16:25Z — owner selects correction, return133444

**Confirmed decision:** Slawomir accepted the investigation and selected mandatory
current handoff/discussion reads, actual managed-turn delivery, and canonical
pass or incomplete-work return before final. He requested a bounded implementation
and recovery plan with exact paths, mechanism and verification budget. Optional
stopReason telemetry is **deferred**. This supersedes the earlier unresolved
choice among the three proposed directions; only the behavioral/delivery
correction is selected. Planning does not authorize this reviewer to implement
application changes, release W133117 or restart services.

**Current state:** snapshot133450 reports W133117 failed since04:05:40, still held
by baton.claude under claim133353/episode133349. The latest author PROGRESS reports
2.54s of77s, with P review allocation8s unchanged. Its five public custody
operations are reported complete; admission/driver wiring, exports, any needed
store support and required regression groups remain. These are author claims,
not an independent implementation review. The next executor must preserve and
reconcile all cumulative run records; no budget reset is implied.

**Delivery revalidation:** ACP bridge source loads accepted role instructions
once before its wait loop, then includes them in every readiness prompt. Editing
the role configuration alone will leave the running bridge with old text.
`MANAGED-TURN-INSTRUCTION-v1.txt` is the proposed exact appended instruction;
`evidence/config-change-proposal.json` binds the observed config bytes and only
two intended JSON changes: impl instruction and generation8 to9. The generation
must be revalidated before execution. Selected existing carrier: canonical
`regen` acceptance followed by an operator-controlled lifecycle replacement,
then proof of the corrected text in the actual managed prompt. No bridge-code
change, dynamic reload, direct transcript injection or raw-store mutation.

**Operational access finding:** canonical `instructions role=impl` as
baton.codex refused because this participant holds only rview. This is expected
role isolation, not a product defect; no alternate identity was used. The
on-disk config proposal is not falsely labelled an accepted instruction read.
Accepted delivery must instead be demonstrated by the configured launcher and
its real prompt. The exact existing role text agrees with the prior retained
prompt. Earlier guessed tools/bin paths were absent; repository discovery
located `tools/infra.py` and the `just start/stop/status MAILBOX` recipes.

**Prepared scope:** `CORRECTION-RECOVERY-v1.md` supplies exact text/path ownership,
ordering, drift refusals, proof conditions and a proposed120s independent
operational verification allocation. `evidence/recovery-preservation-133448.json`
records20 scoped source/test/dossier path entries for W133117, including planned
absence. Only this investigation dossier was written; no release, restart,
configuration acceptance, policy edit or product verification occurred.

## 2026-09-10T04:23:06Z — bounded scope and budget approved, return133489

**Confirmed owner acceptance:** Slawomir approved CORRECTION-RECOVERY-v1.md and
the separate120s allocation:15s author,15s review,90s operations. He assigned
preparation of tuner authorship, independent review and the exact external
operations checklist. Recovery is authorized only after independent review and
all documented preconditions pass. This explicitly supersedes the proposal's
pending-approval wording; it does not waive a review or recovery gate. Telemetry
remains deferred and W133117 bytes/evidence/cumulative spending remain protected.

**Coordination under claim133492:** baton.tuner owns the two repository policy
edits and a reviewable deployment config candidate under this dossier, using
the approved exact role append. baton.codex owns independent review after the
tuner returns W133361 to baton.bug. The live config write/regen and external
lifecycle/recovery belong to baton.slaw's authorized operator after review,
not to the tuner or this managed reviewer. Endpoint roster confirms baton.tune
resolves to baton.tuner, currently idle with no claim. No child Work or parallel
writer is needed for these serial stages.

`OPERATIONS-CHECKLIST-v1.md` is the prepared operator sequence. The tuner must
prepare its named config candidate and manifest as review inputs; these outputs
are not claimed to exist before authorship. The independent review binds their
actual bytes before the operator may use them. Planning did not consume an
author/review verification run or change the live config, P claim or runtime.

## 2026-09-10 — tuner revalidation under claim133517

**Confirmed:** current handoff133514 and complete T133361 discussion assign only
the approved policy edits and a reviewable config candidate to baton.tuner.
The live config still matches proposal SHA256
`b03b92c28f334bd786df3d87ecc660978c1b1a9d13541c0d146d7e15e964e998`, generation8.
All20 W133117 preservation entries match, including the planned absent test.
The two policy files had no pre-existing working-tree diff. The recorded ruling
remains applicable; no superseding scope or authority was found.

**Operational lookup finding:** an initial read of guessed installed
`tools/acp-agent-bridge/{acp_baton_bridge,baton_readiness}.mjs` paths failed with
ENOENT. The retained runtime-source.json supplies the actual installed
`lib/acp-baton-bridge/src/` paths, which were then read successfully. This was an
incorrect lookup, not a Baton defect or an unread required policy. The actual
bridge still loads instructions at line169 before the loop at line315 and
passes them to the prompt at lines506-507. No carrier change is required or made.

The author candidate implements the accepted correction only. Independent
review and actual managed-turn delivery/settlement evidence remain required;
policy text and a config candidate do not establish behavioral acceptance.

## 2026-09-10T04:32:48Z — independent static sign-off, claim133540

Reviewer baton.codex accepted the exact tuner candidate and operations checklist
in review-2026-09-10T04-32-48Z.md. That append-only review binds both policy
files, the49709-byte config candidate, its unchanged live base, manifest,
instruction and recovery checklist. Independent evidence/review-133540.json
confirms only the approved two JSON value changes, exact role append, preserved
policy modes, clean scoped whitespace and all20 unchanged P entries. Live
config remains the original bytes at0600; retained evidence mode0664 is not
an installation mode. No existing test path changed in this correction.

Conservative charges: author1s/15s and reviewer1s/15s; operations0s/90s.
The measured independent check was0.003950455s. Remaining shares14/14/90s are
not transferable. All P budget history/allocations remain separate. No product
test, live config mutation, P release or restart was performed by the reviewer.

Owner133489 already authorizes the reviewed recovery sequence conditionally;
no repeat permission is needed just for that sequence. Operations must still
establish current custody/domain, exact digests, drained/paused dispatch and
external-terminal readiness. Static sign-off is not a claim that those live
preconditions or behavioral acceptance have happened. Return the operator
receipt and actual prompt/read/handoff evidence for confirmation before closure.

## 2026-09-10T04:54Z — actual delivery confirmed; acceptance incomplete

Under claim133683, operator return133681 was revalidated against canonical
events and the new Claude session. Acceptance133600 binds the reviewed
candidate; resume133643 came from paused; claim133645 uses generation9.
The actual prompt contains the exact correction and public results include
current pass133208 and T133117/M133314. This supersedes pending deployment
and delivery status, not the remaining acceptance conditions.

**Open:** no operator receipt/timing ledger is present; full preflight,
preservation, lifecycle exits and90s budget compliance cannot be certified
from event timestamps. P remains active, so handoff-before-final is pending.
**Observed:** wrapped/piped Baton calls include the successful claim; journal
filtering remains; new P tests began without evidenced reconciliation of
historical spending. Previous progress was consumed, but that alone does not
resolve conflicting totals. Exact evidence and limits are in
review-2026-09-10T04-54-00Z.md and its named evidence files.

Return to operations for original receipt and eventual behavioral proof;
do not interrupt P or repeat recovery. Reviewer spending now2/15s,
author1/15s, operations unknown/90s. P spending is not reset or re-certified.

## 2026-09-10T05:02:52Z — owner accepts delivery and disposes historical gaps

**Confirmed decision, return133752:** deployment and actual instruction delivery
are accepted. Missing historical operations receipts, checks and timings remain
explicit evidence limitations unless original records are available; do not
reconstruct proof or count unknown spending as zero. No repeat recovery or
additional operational verification is authorized. This supersedes the prior
plan to require operations to supply proof it may no longer possess; it does
not certify those historical checks or budget compliance.

W133361 remains open pending actual P handoff and canonical no-claim
confirmation before final. Assess command/read deviations separately, and
require reconciliation of all prior and new P verification spending, failures
included, in P handoff/review. Preserve active W133117. Review disposition must
separate the narrow behavioral result from remaining compliance/evidence
limitations. W133361 author1/15s and review2/15s are unchanged at this ruling;
operations is unknown/90s, without new spending authority.

## 2026-09-10T05:06Z — narrow behavioral acceptance proved

**Confirmed under claim133754:** corrected session3138d003 returned W133117
to baton.bug at133765 (05:04:31Z), consumed a canonical no-claim result at
05:04:38.607Z and issued its end_turn final at05:04:54.487Z. Snapshot133775
corroborates unclaimed queued P. This supersedes pending handoff-before-final;
the corrected turn settled without another owner recovery.

review-2026-09-10T05-06-00Z.md recommends owner closure on that narrow behavioral
basis. Full command/read compliance was not achieved: wrapped/piped/batched
calls continued. Historical operational evidence remains limited under133752.
P's9.49s total carries2.54s without resolving prior discrepancies and omits a
failed pytest attempt from its manifest. M133767 explicitly requires complete
reconciliation in P's own handoff/review; no product acceptance or budget reset
is implied. No further operational verification or recovery occurred; W133361
author1/15s, review2/15s and ops unknown/90s remain unchanged.
