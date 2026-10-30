
### The result: completed on its own, R1 and R2 both reproduced then corrected

**The run ended on its own.** Controller `state completed`, `child_started`
true, `child_exited` true, **`child_status 0`**, `elapsed_seconds`
**2689.0656055909994**, `faults []`, `operator_signals []`, `recovery_only`
false. Workload `state settled`, `stopped completed`, `served_seconds`
**2689.199099617** against the 3600s provider ceiling — **910 seconds of
margin** — `finished_at 2026-10-22T16:08:09.721Z`, `stage_states
{implementation: completed}`, one admission, one admitted attempt, zero
`gate_refusals`, zero `held_because`, zero `interruptions`, zero
`cleanup_sweeps`, zero `uncertainty`, zero `unexpected_attempts`, zero
`shortfalls`. The attempt's token: `expired` **false**, `returned` **true**,
**`renewals` 0**, `expiry_judged_at` null. Runtime `destroyed`, cleanup
`retained`, observation `absent` because *"the engine answered … No such
container"*. No fault anywhere in any of the five artifacts.

**The envelope permission is no longer a document claim.** Origin
`2026-10-22T15:23:20.487Z`, `stop_at` `2026-10-22T16:42:20.487Z` = origin +
4740s, token `expires_at` `2026-10-22T16:43:20.487Z` = origin + 4800s, and the
turn used 2689s of it with **zero renewals**. Under the retired 900-second
default this turn would have been cut off at about 900s — exactly as run340352
was at 904.78s and run341360 at 905.18s — **and it would have lost both
corrections**, because the five-module gate alone was not measured until well
past that mark. W333485's accepted correction, consumed through W348979's
corrected binding, is what made this turn possible.

**`collect.py` step 5a, read-only, 0.017s:** five of six artifacts
**present** — workload outcome, controller report, manager snapshot, shutdown
progress, authoring log — `isolated_failures []`, every one of the controller's
four self-named links `found`, no artifact carrying its own temporary, and the
sixth, `shutdown_request`, **absent**, which is correct and names no cause: the
turn returned on its own so no bounded shutdown was ever requested.
`publication_timeout.established` is **false**, which for this vehicle means
*nothing on disk could tell you either way* and **not** "no timeout happened";
there are no parsed publication faults, no other timeouts observed and no
uncorrelated ones. The shutdown progress file names `final enforcement
publication` as the last step **entered**.

**The candidate.** Base `bc925cf5c62d69426ed5862af4d41f4d2a967b0f`, head
**`2d313602e0a82a365f3b0239a9ce1ba91f62c56a`**, content digest
**`sha256:c509bd42d5430dcee4d1b12ded916cdfff903d31754df96867d9cb4a561a8d47`**,
434587 bytes, four custody entries, `state valid`, `disposition completed`,
**`verification passed`**, `acceptance` **`unobserved`** — which is the manager
saying what it is: a retained candidate nobody has accepted. Eleven changed
paths, exactly the candidate's eleven: the four producer files
(`failure_cause.py`, `intake.py`, `attempts.py`, `documents.py`), the focused
producer test module, the three fixture inputs, `test_intake.py`,
`test_maintenance.py` and the extended `W341357-VERIFICATION.json`.

**R1 and R2 were each REPRODUCED AT THE PRODUCTION BOUNDARY BEFORE being
corrected**, which is what `TASK.md` item 1 required and what no earlier turn
had done. From the run's own report:

- **R1** reproduced at `intake.settle_revoked_resource` over a real governed
  generation — claimed, activated, started, runtime attached, token acquired,
  expired by a clock that moved, revoked through the product's own
  `tokens.workspace_governance().revoke`. A fresh A→B→A wrote revisions 0 and 1
  and then **wrote nothing** for the third fresh observation, so the reader
  answered `uncertain-observation` about a runtime just observed quiescent; the
  reverse order left **a stale positive current** while the runtime was
  observed running. Corrected by sequencing an observation on the account it
  was taken after — `supersedes`, which already meant that — in four branches,
  with no contract change and no call-site change. Red first: the existing
  replay case failed `assertEqual(again, first)` on the operation id.
- **R2** reproduced **on every acting path** by injecting
  `ContractRefusal('unavailable','transport')` into `store.transact` for
  `attempt.cessation-outcome` **and nothing else**, placed **after the durable
  intent commits** so the cases cannot accidentally re-prove the previous
  Work's intent-ordering property — every case asserts the intent reads back
  and the outcome does not. Six boundaries measured across reclaim, settlement
  and cancellation, including a dict shape, a closed document and an exception.
  Corrected through one owner, `carry_degradation`/`degradation_of`, with the
  original engine refusal's category, code and message asserted unchanged
  byte-for-byte. Red first: **10 failures** with R1 in place and the R2 call
  sites untouched, with the one path that already carried the member passing
  red — which is what makes the other ten about the dropped return and nothing
  else.

**The complete five-module gate, no skips:** 864 tests OK in 11.026s at the
applied candidate *before* any change, then **892 tests, 0 failures, 0 errors,
0 skips, OK, exit 0, 11.152s** after both corrections, four repetitions between
11.073s and 11.181s, **18.8s of headroom** under the 30s ceiling. Only
`test_attempt_failure_cause` moved, and only upward.

### What I verified myself, and how — no host product test

**I ran no product test.** There is no product-test authority for this Work and
the classification belongs inside the run. What I did is **read-only text
analysis** of the published bytes, and `GATE-CLASSIFICATION.json` labels it as
exactly that rather than as confirmation that 892 tests pass:

- The sealed content manifest agrees **member by member** with the four custody
  files I copied — `change.patch` `044d58bc…`, `objects.bundle` `0a5fdecf…`,
  `result.json` `bc35d7c5…`, `verification.txt` `2b49d85a…` — under tree digest
  `c509bd42…`, and the patch's 11 `diff --git` sections equal
  `result.json`'s 11 changed paths.
- **The focused module's case counts reproduce independently.** Counting
  `+def test_` names in `recovery-345822/candidate.patch` and in this run's
  patch gives **63** and **91**, delta **+28** — the run's own per-module
  figures — and **every one of the 63 candidate case names is still present**.
  Nothing was deleted to make room.
- **The one existing case that changed is input-only, as reported.**
  `test_a_REPLAY_of_a_SUPERSEDED_revision_writes_NOTHING_MORE` now passes
  `observed_after=one["supersedes"]` and keeps a binding it used to discard;
  its name and **all four assertions are byte-identical**, with a docstring
  paragraph added. One note for the reviewer rather than a claim of mine: the
  coordinate supplied is that record's own `supersedes`, so for revision 0 it is
  whatever an empty chain's tip is — worth reading in the recorder's bytes.
- All **11** evidence copies re-hashed against their sources in the live root:
  **11 of 11 agree**. 28 files indexed with digests in
  `evidence/run-352156/INDEX.json`.

### What this run did NOT establish, and one reporting gap

The run's own report lists what it did not establish and I am not softening any
of it: **no acceptance**; not the full joined twelve-module gate, the
installed-bundle proof or the ordinary status/report integration, all of which
parent W333486 owns and none of which was run; not a live engine, provider or
container inside the reproductions, which drive the production entry points
with the adapter, agent and governance injected at the same seams the
already-accepted cases use; not the cause of what filled the mount in run345388,
which remains **unknown** and which the turn explicitly refuses to let its own
`test_secrets` storage finding stand in for; not the **194** pre-existing
out-of-gate failures, measured byte-identical in both arms across eleven
further modules and therefore unmoved — and also unfixed and uninvestigated;
and not whether the parent's seam reads the degradation off an exception, since
no downstream consumer of that shape exists yet.

**One reporting gap I found rather than was told, and it is the turn's.**
`TASK.md` item 6 asks the turn for the expiry and cessation facts **it
positively observed from inside**. The extended report's top-level
`lease_and_cessation_facts_POSITIVELY_OBSERVED_FROM_INSIDE` section still
describes the **first** turn — 549s elapsed, a 900-second lease, the 600/720
targets — and the turn did not add its own. It is disclosed collectively (the
new section opens by saying the sections above are the first turn's and are left
as they were), so this is a missing section rather than a false one, and the
turn's correlation keys and monotonic origin are recorded. But the 900-second
figure in that older section is retired, and a reader who stops there would take
it as current. Flagging it rather than editing the candidate's bytes, which are
the reviewer's to judge.

A third classification defect was found while reproducing R2 — a transport
refusal reported as a collision — and corrected with a case; the turn reports it
as observed rather than looked for, and claims **no** production occurrence.

### Cost and preservation

Measured host-side subtotal this claim: input check 0.067s, capability 0.081s,
stage 0.076s, bootstrap 0.649s, bind 0.377s, boundary preflight 0.379s, collect
0.017s — **about 1.65s** — plus one discarded boundary pass that failed on my
own `CompletedProcess` assumption, plus the read-only analysis above. **The run
itself: 2689.07s controller elapsed, 2689.20s provider served.** Child
cumulative: measured subtotal about **5702s** plus unknowns (about 3011s
before this claim). The parent's about 2253s stays with the parent. Campaign
provider served now about **7362s**. Gate measurements 5, the last two passing.
**Product tests executed by me on the host 0**; Jobs 1; attempts 1; runtimes 1;
provider calls 1; engine calls 6 read-only across one capability check and one
boundary preflight, plus the run's own; credential values read **0**;
version-control mutations **0**; old-instance mutations **0**; retries **0**;
rebinds **0**.

The new root `/home/sl/baton-instances/durable-capture-w341357-352156` is
preserved unmodified after collection, and all ten earlier roots are untouched.
Every artifact a later turn needs is in `evidence/run-352156/` under the
canonical dossier rather than only in `/tmp`, per M352206: the five published
final artifacts, the candidate's four custody files and its sealed manifest, the
extended `W341357-VERIFICATION.json`, the collection, both preflight reports
and the three check programs, the input check, the three preparation logs,
`PREPARED.json`, the generated `AUTHORING-COMMAND.json`, the launch record and
the controller's own streams.

**The plain statement this turn is entitled to make and no more:** the selected
invocation started, held its envelope-derived permission for 2689 seconds with
no renewal, reproduced both withheld defects at the production boundary before
correcting either, passed the complete five-module gate with no skips, and
retained a digest-bound candidate the manager marks `verification passed` and
`acceptance unobserved`. **Nothing here is accepted.** R1 and R2 now need
independent **producer byte review** — the thing every earlier turn was short
of — and parent W333486 still owns the joined status/report integration, the
twelve-module gate, the installed-bundle proof and final acceptance under
dependency341370.
