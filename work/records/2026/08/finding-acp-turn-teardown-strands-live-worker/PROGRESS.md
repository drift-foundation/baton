# Progress

## 2026-08-31 — operator recovery completed

The operator stopped container
`afed4c76aebe339911ab353021227f94cb8c635e9b46ed1e4ba2f642f4d7d334`.
Docker reported `exited`, `running=false`, exit code 137, with finish time
`2026-08-31T18:29:01.079874978Z`. The operator then released exactly W51487,
expected Handler `baton.claude`, episode 55530. Canonical detail now shows no
Handler, phase `queued`, and fresh assignment episode 55726. The retained
`/tmp/w51487/run7/` evidence remains untrusted and was not removed.

## 2026-09-01 — first implementer round (`baton.claude`, W55705 impl claim)

**Plan item 4 is implemented. Item 5 is asked rather than chosen, and item 6
is NOT done — that is the honest state and the reason is below.**

New file `tools/acp-baton-bridge/src/acp_settlement.mjs`; wiring in
`src/acp_baton_bridge.mjs`. The existing suite is green at **89/89**, the
recorded baseline, so nothing accepted was broken.

### What landed

`AcpSettlement` reuses the sibling `QuarantineStore` — made generic for exactly
this second fence — with suffix `.acp-settlement.json` below the configured
`stateDir`, keyed by the participant claim slot rather than by the agent
process or the replaceable ACP session. It restores BEFORE the first wait and
the first `idle`, treats a damaged marker as fenced rather than absent and
preserves its bytes, classifies one canonical `wait timeout=0` read into
`claimed`/`secondary`/`held`/`released`/`unreadable`, fails closed on
unreadable and on authority-UUID drift, commits the marker BEFORE any
asynchronous publication, publishes `failed(internal)` instead of `idle`, files
one sticky incident and retries it when `incident()` answers false or throws,
and clears only on a canonical released answer whose delete was confirmed.

Settlement runs after EVERY ACP turn outcome — the ordinary successful return
included — because ACP has no semantic completion status and a returned prompt
is a transport fact.

### The conflict I found, and the refinement I did not make silently

**W55705's acceptance as written and W11910's accepted correction cannot both
hold.** This record says to retain later readiness whenever a claim survives.
W11910 added `test("a claimed-Work recovery prompt that FAILED is delivered
again")` precisely because suppressing the re-offer of a Work the participant
already holds left a live claim with no wake and no retry until somebody
restarted the process — "the exact restart-dependent stall this Work removes."
Retaining readiness on a surviving EXACT claim reintroduces it. My first cut
did exactly that and broke that test plus four others.

The division that keeps both true is whether ANYBODY WILL BE WOKEN:

    claimed      the authority is still offering this Work to this
                 participant, so re-delivery IS the recovery. `idle` is still
                 withheld and the incident is still owed, but readiness is not
                 retained.  -> verdict `recoverable`
    secondary    the one slot is occupied by something this offer cannot
    held         become; retain it and spend no turn.  -> `stranded`
    unreadable   nothing is known; fail closed.        -> `stranded`

Applied to the observed incident this is still the correction: run7's W51487
was `claimed`, so the bridge would have published `failed` with the surviving
claim named and filed an incident, instead of publishing `idle` and saying
nothing. The false capacity and the missing durable notice — the two facts the
finding calls the defect — both go away.

**This is a REFINEMENT OF THE ACCEPTANCE and it is the reviewer's to accept or
overrule.** I implemented it rather than shipping something that breaks an
accepted prior correction, and I am flagging it rather than letting it pass as
bookkeeping.

### Item 5 is asked, not chosen

M57668, non-blocking so item 4 could proceed. The prerequisite is real: this
deployment's runtime projection carried `action_owner: null`,
`RuntimePublisher.incident()` refuses an ownerless incident and returns false,
and ACP config treats `runtime.actionOwner` as optional — so the settlement
correctly fences and then retries an incident that can never be filed here. I
did NOT add a startup refusal: refusing startup is a deployment-breaking change
and is not mine to choose.

### Item 6 is NOT done

The finding's regression matrix — no-claim, exact/secondary/unreadable,
successful and failed prompts, marker restart/corruption/recovery, publication
concurrency and retry, later readiness retention, a newer episode, detached
runtime survival, composed process-domain failure, and the absence of automatic
kill/release — has not been written. The 89 passing tests are the PRE-EXISTING
suite proving nothing accepted regressed; they are not evidence for this
Work's own behaviour.

I stopped here rather than starting that matrix and leaving it half-written.
A security fence with partial coverage that reads as covered is worse than one
that says plainly it is uncovered. The module is structured for it — `readSlot`,
`store`, `now` and `runtime` are all injectable, and `classifySlot` is exported
and pure — so the matrix is additive work against a stable seam.

### State

Awaiting review of the settlement design, the W11910 refinement above, and the
item-5 ruling. Passing back rather than closing.

## 2026-09-01 — second implementer round (`baton.claude`, W55705 impl claim)

**All four [P1]s from `review-2026-09-01T03-41-20Z.md` are corrected, plan item
6's matrix is written, and plan item 5's approved startup refusal is
implemented.** Files: `tools/acp-baton-bridge/src/acp_settlement.mjs`,
`src/acp_baton_bridge.mjs`, `test/acp_baton_bridge.test.mjs`.

The reviewer is right on all four, and three of them are the same mistake: I
wrote a value down and then did not let it decide anything.

### [P1] A stranded slot now stops the envelope, not the action

`break`, not `continue`, on both the returned-prompt and the failed-prompt
settlement paths. The outer fence check runs once per envelope, so a `continue`
let the next fresh action revalidate against its OWN successful read and start
a turn — after this bridge had just failed to prove the claim slot safe. That
is fail-open for exactly the unreadable and drifted cases the fence exists for.
Every remaining action is retained: no prompt, no `markPresented`, no
`markWithdrawn`.

### [P1] Fence IDENTITY is preserved through the read

The old retry saved one boolean, set `this.fence = null`, recursed, and copied
the boolean back afterwards. All three of the reviewer's failures follow from
that ordering, and all three are gone:

- `#read` now takes the comparison base as an OPERAND (`against`) instead of
  reading `this.fence`, so a retry compares the new answer with the authority
  the fence was actually taken against.
- An `authority-drift` or `unreadable` answer against an existing fence changes
  NOTHING except the fence's `verified` bit. "I could not ask" is not a new
  fact about the slot, and minting an `unreadable` fence there would give one
  stranded claim a second identity, a second incident and no recorded
  authority. A drifted read records what it saw as `drift` and never adopts it.
- A genuine SUCCESSOR — different authority, Work, episode, action key or
  correlation — mints its own fence with `incidentFiled: false`. It inherits
  nothing.
- `#fileOnce` compares identity BEFORE applying an acknowledgement, so a
  publication that lands after its fence was replaced is logged and dropped
  rather than suppressing the successor's own incident.
- `fileIncident` is serialized on one in-flight promise, because `settle` and
  `reconcile` can both reach it and two publications for one fence is two
  incidents for one stranded claim.

The same identity rule now governs `reconcile`, which is where the reviewer's
W1/episode-11 → W2/episode-22 case lived: a different occupant is a successor
and owes its own incident.

### [P1] A restored marker meets the authority before anything is delivered

`fenced()` answered false for a `claimed` marker, so a restart skipped
`reconcile()` entirely and could deliver on the strength of a fence taken
against another authority. A fence now carries `verified`, false for anything
restored from disk, and `fenced()` is true until one canonical read confirms
the recorded authority. Only a MATCHING exact claim enters the W11910
redelivery path; drift, a missing `authority_uuid` and an unreadable answer all
stay fenced with the original authority intact.

A missing authority in the answer is now drift rather than a pass. A projection
that dropped the field cannot confirm the answer is about the authority the
fence was taken against, and the record's boundary is explicit that this fails
closed.

### [P1] Marker persistence decides something now

- The initial `store.save` result is what `fenced()` reads: an uncommitted
  marker strands the lane rather than looking durable, because a restart would
  find nothing and deliver into the same occupied slot.
- The acknowledgement save is checked. It sets `incidentFiled` in memory — this
  process must not publish twice — but marks the fence NOT durable, so a
  restart that would file a duplicate is fenced instead.
- A `clear` nobody could confirm keeps the fence on BOTH paths. `reconcile`
  already did this; `settle`'s release path did not, and silently left a marker
  on disk that a restart would resurrect.

### A fifth defect the matrix found on its own

`reconcile` classified its canonical read against the fence's **occupant**. For
a `secondary` fence the occupant is a DIFFERENT Work from the one delivered, so
the next reconcile found that occupant "claimed", called it a state change, and
re-admitted delivery into a slot that had never freed. The fence now records
the delivered OFFER (`offered: {work, episode, actionKey}`) apart from the
occupant, and reconcile asks about the offer. This was latent in the first
round and was not in the review; the retention test is what exposed it.

### Plan item 5: the approved startup refusal

M58455 approved it and it is pinned in the finding, so `runBridge` now refuses
before `loadInstructions`, before the runtime lease and before the first wait
when `runtime.actionOwner` is absent. The refusal states the reason — a
surviving claim owes one durable incident to a configured recovery participant
and an ownerless one is refused — and says the owner is never inferred.

The test rig gains `runtime: { actionOwner: "baton.slaw" }` so every case
describes a startable deployment; the two cases that are ABOUT the refusal pass
`runtime: null` and `runtime: { provider: "claude" }`. No existing assertion
was changed or weakened.

**One thing I did NOT do.** A deployment may still configure the owner equal to
the runner participant, which makes the runner the addressee of its own
incident — the deadlock M57668 named. Refusing that is stronger than the pinned
ruling, so it is flagged for the reviewer rather than implemented.

### Plan item 6: the matrix

Thirty W55705 cases; the suite is 119, up from the 89 baseline. Grouped as the
finding asks:

    the three verdicts, end to end through runBridge
      no surviving claim -> idle and presented
      exact claim survives a RETURNED prompt -> failed, one incident, no idle
      exact claim survives a FAILED prompt -> delivered again, no idle,
        and ONE incident across both turns
      a secondary claim -> stranded, offer retained, one turn only
      a newly stranded slot stops the rest of the same envelope (returned)
      a newly stranded slot stops the rest of the same envelope (failed)
      strand -> retain -> canonical release -> delivery resumes

    the state machine
      a recoverable retry keeps identity, instant and authority; files once
      a retry against another authority stays fenced and adopts nothing
      an answer naming no authority is drift, not a match
      an unreadable answer keeps the fence rather than minting a second
      a successor mints its own unfiled incident
      the same Work under a NEWER episode is a successor, not a release
      a late acknowledgement is never transferred to a successor
      the incident is retried when publication refuses AND when it throws
      two concurrent observations file one incident

    persistence and restart
      an uncommitted marker strands the lane
      an uncommitted acknowledgement is not reported durable
      a clear nobody could confirm keeps the fence (reconcile and settle)
      a settled release retires the marker a restart would find
      a restored marker is fenced until the authority matches; a drifted
        restart delivers nothing, through runBridge
      a damaged marker stays fenced and its bytes are preserved
      an exact canonical release clears a restored marker

    the boundaries this Work does not cross
      a delegated runtime locator is named ONLY when supplied
      the module reaches for no child process, no docker, no kill; the
        remedy it publishes is an operator `release` that says to prove the
        runtime absent first
      a process-domain teardown failure is the STRONGER fence: it is fatal,
        no settlement runs behind it, and no idle is published

    the incident's owner
      an ownerless bridge refuses before the lease and before the first wait
      a configured owner starts ordinarily

### Mutation check

Fifteen mutations of the corrected guards; all fifteen caught.

    CAUGHT  a stranded returned turn only skips its own action
    CAUGHT  a stranded failed turn only skips its own action
    CAUGHT  an ownerless bridge starts anyway
    CAUGHT  an uncommitted marker still looks durable
    CAUGHT  a restored marker is deliverable before any read
    CAUGHT  the authority comparison is dropped
    CAUGHT  an unnamed authority counts as a match
    CAUGHT  every fence is the same fence
    CAUGHT  a late acknowledgement is applied to whatever is current
    CAUGHT  the acknowledgement save result is ignored
    CAUGHT  reconcile asks about the occupant instead of the offer
    CAUGHT  a released slot leaves its marker on disk
    CAUGHT  reconcile clears in memory whatever the delete said
    CAUGHT  concurrent publications are not serialized
    CAUGHT  an opaque answer re-mints the fence

**Three started as MISSES and the TESTS were wrong, not the mutations.** The
failed-path `break` had no case at all — I had covered only the returned path,
which is half a correction. And the settle-path `clear` guard was unprovable
twice: deleting the guard still deletes the marker in the ordinary case, so
only a FAILING delete can show that the fence survives one. Both now have their
own cases and both mutations are caught.

### The ledger discrepancy I am not fixing

The scheduling refinement is pinned in `FINDING.md` as approved and dated
2026-08-31, and I implemented what that text says. On the ledger, obligation
seq 58475 (owed by `baton.decide`) is still **pending**, and `PLAN.md` item 8
cited M58475 as the approval when M58475 is the message that requested it. I
corrected the plan's wording and recorded the discrepancy in the finding.
Discharging another participant's obligation is not mine to do.

I also marked the finding's **Regression boundary** bullet 2 explicitly
superseded: it still said a returned prompt with a surviving exact claim gets
"no presented acknowledgement", which the refinement reverses. Two live rules
that contradict each other are worse than either alone.

### Verification

    tools/acp-baton-bridge          npm test        119 tests, OK  (89 before)
    tools/codex-event-bridge        npm test        430 tests, OK
      including test/failed_turn_settlement.test.mjs  54 tests, OK

No automatic runtime kill, credential action, partial-output acceptance or
claim release was introduced; one case asserts that as a property of the
module's source and of the remedy it publishes.

### State

Awaiting independent review. Passing back rather than closing.

