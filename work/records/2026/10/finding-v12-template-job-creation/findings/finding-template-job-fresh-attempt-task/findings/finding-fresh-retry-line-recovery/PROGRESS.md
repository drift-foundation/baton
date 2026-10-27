# Implementation progress

## claim365081 — the supported recovery APIs, revalidated; one spec conflict pinned

Answers the bound `FINDING.md`: revalidate current supported recovery first,
and if a concrete specification conflict is found, pin exact clauses and
options for owner approval rather than changing semantics. That is what this
claim did. Baseline is the parent's `candidate-364962` (manifest
`7a2f1b734a1474d2e4e6df5b5759875df65c790c5c5c049055ffc2c733dd6812`) over base
`19f02ce1`; this child's candidate is `candidate-365081/` and **no product
byte is changed in it**.

### Why the retry's preparation is refused, in full

`tests/tools/test_fresh_retry_line_recovery.py`, **12 cases**, over the
parent's own fixture:

1. **An `unable` implementation ending still freezes the line's checkpoint.**
   `review_driver.end_implementation`'s step EIGHT is
   `review_cycles.freeze_checkpoint`, unconditionally, and the function's own
   comment says so: "An `unable` or `cancelled` turn skips straight to eight
   and nine, which are the acts that actually end an attempt." Freezing moves
   the line to `review-ready`. Asserted: `line.state == "review-ready"` with a
   `frozen` checkpoint.
2. **No review can ever attach to it.** The attempt answered `unable`, so
   nothing was published and the Job's own review stage is `blocked` — its
   gate needs a completed implementation. Asserted: zero rows in
   `review_attachments`, and the stage projection is exactly
   `{implementation: exceptional, review: blocked}`.
3. **The writer that produced the checkpoint is revoked** by that same freeze,
   so the line is not `writing` either. Asserted: no `line_writers` row is
   `active`.
4. **`grant_writer` admits a writer only from `idle` or `correction-ready`**
   (`review_cycles.py:1848-1864`), so the retry's preparation is refused
   through the composition the serving loop uses: "line state 'review-ready'
   does not admit a writer".

### Every supported operation, and the precondition it refuses on

- `grant_writer` — the state itself, as above.
- `record_verdict` — takes an `attachment_id`, and there is no attachment;
  manufacturing one is forbidden by the FINDING and by this claim.
- `restore_abandoned_correction` — its own docstring is about the line still
  being `writing` with an `active` writer after a declared abandonment. Here
  the writer is revoked, the line is `review-ready`, and no abandonment was
  declared. Refuses.
- `integration_checkpoint` — answers only for an `accepted` line; it reports
  absence and changes nothing (asserted as the absence it is, after an earlier
  draft of mine expected a refusal).
- `audit_checkpoint` — the one operation that accepts this state, and it is a
  READ: the line is byte-identical before and after.
- `record_progress` — a writer's own journal; there is no writer.

So **no supported recovery advances this line**, and the FINDING's "if
existing mechanisms suffice, provide connected evidence" is answered: they do
not.

### The conflict, pinned for an owner ruling

A line left `review-ready` by an ending that produced nothing to review can
never admit another writer: no correction round (needs `correction-ready`) and
no fresh retry (needs `idle` or `correction-ready`). Every exit requires a
verdict, and a verdict requires an attachment that this Job's own blocked
review stage will never create. The three ways out each change a rule, which
is why none is implemented here:

**Option A — the ending's freeze becomes disposition-aware.** For a
non-publishable disposition, end the assignment without asking for a review:
`review_driver.end_implementation` steps 7-8 (its `_publishable(disposition)`
branch already distinguishes them for the publication), and
`review_cycles.freeze_checkpoint`'s transition to `review-ready`. My own
reading favours this: an ending with no candidate should not leave a review
pending, and the asymmetry is already written down one step earlier.

**Option B — a supported operator transition out of a frozen-with-no-review
line**, returning it to `correction-ready` at the retained checkpoint. This is
exactly the shape `restore_abandoned_correction` has for the `writing` case
(`review_cycles.py:3104-3160`), and would be its sibling for this one.

**Option C — `grant_writer` admits a fresh retry from `review-ready`** when it
names the current checkpoint (`review_cycles.py:1853-1861`). This weakens the
review fence, which is why it needs a ruling rather than an implementation.

Each option is a change to an accepted rule about reviews and lines, not an
internal design choice inside this outcome, so I have stopped at the pin.

### What this claim did NOT do

No verdict was manufactured, no checkpoint erased, no row edited, no cleanup
forged, and no product byte changed. The original Work, specification, task
identity, failed-attempt evidence and attribution are untouched, and the
pending review — illegitimate though it is — is left exactly as the product
left it.

### Verification

Candidate root `/tmp/w365081`; `PYTHONPATH=src:.`

- **`tests.tools.test_fresh_retry_line_recovery`: 12 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **Four tools suites** (this one, retry_task_lineage, connected_creation,
  job_task_delivery): **119 cases, OK.**

### Cost

Reading `review_cycles`'s whole public surface and its line states,
`grant_writer`'s admission, `restore_abandoned_correction`'s preconditions,
`audit_checkpoint`, `integration_checkpoint`, and
`review_driver.end_implementation`'s step order. One probe, kept in the
evidence directory, for the line/checkpoint/attachment/writer state after an
`unable` ending. Test runs: the new suite four times (three failing — a
borrowed `setUp` whose zero-argument `super()` cannot cross hierarchies, a
`grant_writer` call refused earlier for operands the composition derives, and
an `integration_checkpoint` that answers rather than refuses); the tools group
and `tests/job_manager` once each. No live provider, no container engine, no
deployed-instance mutation, no version-control operation.

### Boundaries

No Git operation of any kind, and no fixture that performs one was run. The
canonical `v12/python` tree is byte-unchanged, and so is every inherited
product byte in this candidate. The ancestors' candidates and evidence and
this dossier's `FINDING.md`/`PLAN.md` are untouched; I wrote
`candidate-365081/`, `evidence/claim-365081/` and this file.

## claim365155 — the recovery, implemented; the retry reaches both runtimes

Answers review 2026-10-27T00-45-35Z, which did **not** accept the owner gate
my previous claim proposed and told me to proceed: "Implement the bounded safe
recovery and prove the original retry reaches its implementation runtime and
independent review runtime." Baseline is this dossier's own `candidate-365081`
(manifest `a7c59777e448b06c4d8b09654519160048d0b1103268d911f161a5675d665664`)
over base `19f02ce1`; this claim's candidate is `candidate-365155/`, which
changes **three product files** and three test files.

### The change, in two parts

**One. `review_cycles.release_writer`** — new public operation. It does what
`end_implementation`'s step eight owes for a round that produced nothing:
revoke the quiescent writer and fence its assignment. It composes no
checkpoint, never calls the profile, and touches no output, receipt or
retention — so the line returns to `correction-ready` when a frozen checkpoint
is retained and to `idle` when there is none, which is where the last round
that produced something left it. `grant_writer`'s admitted states are
untouched, no verdict is invented, and its exclusion is the freeze's: this
attempt's writer, at the named generation, active, on a line still `writing`
at the same current checkpoint, with a quiescent terminal attempt.

**Two. the ending is disposition-aware** — `end_implementation`'s step eight
freezes when `_publishable(disposition)` and releases otherwise, which is the
rule `_publishable` already states one step earlier for the publication. Both
resume entries (`_resumed_implementation`, `_cleaning_implementation`) take
the same branch, proving the release instead of a checkpoint. The ending
document gained one member, `released`.

### The defect my first cut introduced, and how it was found

The release performed its fence AFTER the write and returned it to nobody. But
ending an assignment is not evidence the container is gone, so the Authority
installs `runtime-quiescence:<generation>` in that same transaction — and
`stage_execution._fenced_gate` decides owedness by reading the fence off the
ending's answer. With no fence in the answer, no discharge was ever asked for.
**The Work stayed gated for ever**: a dead end one step past the one this Work
was created for, with the retry's offer deferred on "an offer is issued only
against open, queued, unclaimed, ungated Work". A probe over the real pool
found it (`evidence/claim-365155/probes/gate.py`), not a test.

The correction is three things, and the ordering is the design:

1. the fence happens **before** the release commits and travels **inside** the
   committed answer, so a replay carries it (`freeze_checkpoint` keeps it on
   the checkpoint row for the same reason; a release has no such row);
2. the writer and line preconditions are asked **before** the fence as well as
   inside the write, because the fence is irreversible and a `review-ready`
   line holds material offered for a legitimate review;
3. the operation's own replay is asked **before** any mutable fact is proved,
   so a resumed ending answers without re-proving a runtime the cleanup has
   since destroyed. The first version proved quiescence first and refused its
   own replay with "requires the exact attached runtime to be positively
   quiescent".

`_fenced_gate` and `_fence_operation` in `tools/stage_execution.py` each
learned the one new pair, `("released", "fence")`.

### The milestone, measured

`tests/tools/test_retry_task_lineage.py` (**24 cases**), over the
two-producer pool, every act the serving loop's:

- **the prior ending's gate is discharged** —
  `Authority.project_work(work)["gate"]` is `None`, the committed discharge is
  `gate_discharge_of(control, first_attempt)["gate"] == "runtime-quiescence:1"`,
  and the retry's own attempt owes none yet;
- **the released line admits the retry's own writer** — one line for the Work,
  state `writing`, no `line_checkpoints` row at all, and the two writer rows
  are the two rounds: the first attempt's `revoked`/`released` and the retry's
  `active`;
- **the retry reaches its own implementation runtime** — stage `waiting` on
  the spare producer, a second attempt row with `execution_runtime` `running`
  and a runtime id, while the first stays `destroyed`;
- **the retry reaches its own independent review runtime** — its real turn
  publishes, so *that* round's ending takes the freeze branch: the line is
  `reviewing` at a `frozen` checkpoint, the attachment over that checkpoint is
  `active`, and a **third** attempt is `running` for the review stage;
- **the excluded round's material is untouched by all of it** — asked at the
  end, after three runtimes: `unable` / `retained` / `sealed`, its assignment
  participant unchanged, and its own task still in its own input root, which
  is the one the retry inherited.

The **one-producer** pool's case was *restored* to its original assertion
rather than retargeted: there the retry is `offered` and its claim defers on
"route 'rview' does not resolve to 'baton.claude'". The release changed where
that case passes through, not where it stops (`probes/single.py`).

### Negative and durability regressions

`tests/tools/test_fresh_retry_line_recovery.py` (**12 cases**), rewritten from
the previous claim's diagnostic reproductions to the new truth:

- an `unable` ending leaves an `idle` line, no checkpoint, no attachment;
- the writer is revoked with reason `released`;
- the first attempt's outputs and stage projection survive it;
- **a published round still freezes and waits for its review** — the release
  must not be a way past a legitimate pending review;
- `release_writer` **refuses** that round, naming the writer the freeze already
  revoked, with `("refused","precondition")` — and **nothing is journalled by
  the asking**, which is how "before any effect" is proved rather than
  asserted (the fence commits its decision to the journal before the Authority
  is asked, so an unchanged operation count is an unasked Authority);
- unknown writer, stale generation, and a different reason for the same writer
  each refuse;
- the release the ending performed **replays its own answer**, fence included;
- **the whole ending is re-enterable** — `end_implementation` called again
  with the composition's own recorded operands answers the identical document,
  proves the release rather than a checkpoint, and two further re-entries
  change no row in `line_writers`, `line_checkpoints`, `review_lines`,
  `review_attachments`, `outputs`, `retentions` or `operations`.

Two cases the previous claim's suite had were **dropped with their reason
recorded in the file**: one would have called `grant_writer` for the retry
directly, which needs an attempt row only `start` writes; the other collides on
`grant_writer`'s writer-derived operation id. Neither could be asserted
honestly, and what they were for is asserted from the line's own record.

`tests/job_manager/test_review_driver.py` gained the new `released` member in
`test_the_resume_answers_the_ordinary_endings_document`, which is the case
that pins the two endings' documents member for member.

### Verification

Candidate root `/tmp/w365155` (whole `v12/` minus `node_modules`, v12 level
kept); `PYTHONPATH=src:.`. Full provenance in
`evidence/claim-365155/HOW-THESE-WERE-RUN.txt`.

- **`tests.tools.test_fresh_retry_line_recovery`: 12 OK.**
- **`tests.tools.test_retry_task_lineage`: 24 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **The five non-version-control tools suites of this dossier's scope: 151 OK.**

**One open verification gap, named rather than passed over.**
`tests/tools/test_stage_execution.py` covers the two `tools/stage_execution.py`
readers I changed, and that suite composes real version control — its own
docstring says "a real version-controlled checkout ... from a real nominated
source". My role forbids mutating version-control operations and the
prohibition is not scoped to this repository, so I did not run it;
`TheDischargeReceiptIsCommittedWithItsOwnKind` and
`TheComposedEndingIsOrderedAndSettledFromItsOwnRecord` are the reviewer's to
run. What those readers now do is proved here instead through
`gate_discharge_of` and `Authority.project_work`, which is evidence about the
behaviour and not a substitute for those classes.

I also started broad discovery runs over `tests/` and `tests/manager` earlier
in this claim before recognising the above, and stopped them. No
version-control repository was created by them and their results are not
attributable to this change in a partial scratch root; both facts are
substantiated in the evidence file.

### Cost

Reading `_fenced_gate`, `_fence_operation`, `_discharged`,
`finalize_quiescent_assignment`'s documented order, `_finalization_record`,
`freeze_checkpoint`'s fence recording, and both resume entries. Three probes,
kept. Test runs: the recovery suite about ten times, the lineage suite six,
`tests/job_manager` four, the five-suite tools group once, plus the two broad
runs that were stopped. No live provider, no container engine, no network, no
credential, no deployed-instance mutation, no version-control operation.

### Boundaries

No version-control operation of any kind, and no fixture that performs one was
run to completion. The canonical `v12/python` tree is byte-unchanged. The
ancestors' candidates and evidence, this dossier's `FINDING.md` and `PLAN.md`,
and `candidate-365081/` are untouched; I wrote `candidate-365155/`,
`evidence/claim-365155/` and this file. `grant_writer` was not broadened, no
verdict was manufactured, nothing offered for review was reopened, and no
unresolved-runtime hold was cleared by hand — the one that cleared is the prior
ending's own `authorize_cleanup` positive-absence proof, carried by the act
that always owed it.

## claim365537 — R1 eligibility and R2 replay stability, both reproductions closed

Answers review 2026-10-27T01-42-10Z, which confirmed the runtime milestone and
requested two changes. Baseline is this dossier's own `candidate-365155`
(manifest `cd89dbce2314ac702c466f680fb4d0ae71ed65bbe05fffc4c2c50c9dcb24c31e`)
over base `19f02ce1`; this claim's candidate is `candidate-365537/`, **one
product file changed** (`worker_manager/review_cycles.py`) and two test files.
`review_driver.py`, `tools/stage_execution.py` and `test_review_driver.py` are
inherited unchanged.

### R1 — the release now proves what it is named after

The reviewer is right and the reproduction is exact. `_quiescent_completed`
rejects only `none`, so `completed` passed every check `release_writer` made:
the writer was `active`, the line was `writing`, the attempt was quiescent, and
the caller's reason string is not a proof. `completed_probe.py` stopped the
successful retry at its own `freeze_checkpoint` call and released that writer
instead — fencing the assignment and returning the line to `idle` with a
candidate sealed. Testing refusal only *after* a published round has frozen
misses that interval entirely, because the freeze is what revokes the writer.

The fix is one refusal, placed before the fence, over the authoritative record:

    if attempt["worker_disposition"] not in NO_CANDIDATE:
        raise ContractRefusal("refused", "precondition", ...)

`NO_CANDIDATE = ("unable", "plan-rejected", "cancelled")` is **enumerated, not
subtracted** from `schema.DISPOSITIONS`, so a fifth worker answer added to that
vocabulary refuses a release rather than silently becoming releasable — which
is the direction a safety boundary has to fail in. A case pins the complement
so the addition is visible rather than silent.

**The recorded disposition is the whole proof, and I did not add a second
check that cannot fire.** `output`'s own rule is "the disposition is COMPARED,
not accepted" — a seal must declare the disposition the attempt axis already
recorded — and that axis is terminal-once, every answer beyond `none` having an
empty successor set. So no sealed result can disagree with it and the fact
cannot move under the fence. A `completed` round with nothing sealed yet is
refused here too, which is precisely the interval the probe found.

### R2 — the replay identity is immutable intent only

Also exactly right. The signature carried `current_checkpoint_id` and the
`returning` state inferred from it, and both move when the next round freezes.
So a re-asked identical release recomputed a different signature and refused
its own committed operation; `replay_probe.py` reproduces it after the retry's
review has started. This is `_frozen_checkpoint`'s own recorded correction —
"`current_checkpoint_id` is MUTABLE and moves every time a later round
freezes" — applied to the operation that needed it next.

The operands are now `{writer_id, generation, line_id, reason}`: the caller's
intent and this writer's immutable facts. A changed generation or reason is a
different intent and still refuses. `returning` is decided **inside** the write
from the row under the lock, and the stale-current-checkpoint check stays
inside `act` where it belongs — a replay never reaches it, so an old release is
answered rather than re-judged against a checkpoint a later round froze.

### Verification

`tests/tools/test_fresh_retry_line_recovery.py` grew from 12 to **25 cases**.
The thirteen new ones are the behaviours the review named:

- **before-freeze completed refusal** — driven the reviewer's way through the
  real successful retry, intercepting at the freeze: the writer is `active`,
  the line is `writing`, the disposition is `completed`, the release refuses
  `("refused","precondition")` naming the candidate, and the line is still
  `writing` afterwards. The same case then delegates to the real freeze, so it
  also says the round it protected **still reached its review**.
- **the vocabulary pin** — `set(schema.DISPOSITIONS) - set(NO_CANDIDATE)` is
  exactly `{"completed"}`.
- **exact replay after a newer checkpoint** — the old release answers the
  ending's own committed `released` document byte for byte (`json.dumps`
  sorted), carrying `idle`, no checkpoint and gate `runtime-quiescence:1`
  while the line is `reviewing` at the later round's frozen checkpoint.
- **the newer state is neither consulted nor changed** — line, checkpoints and
  attachments are row-identical before and after the replay.
- **reopen** — a fresh `ControlStore` incarnation answers the same document
  and leaves the newer state alone.
- **changed reason / stale generation after the later checkpoint still
  refuse**, and still change nothing.
- **a live runtime with no answer yet refuses** — the retry's own container is
  `running` with disposition `none`; the refusal is the quiescence half, and
  the writer, the line and the attempt row are unchanged after it.
- **a session for another participant refuses at the releasable moment** —
  asked by intercepting the composition's own release call, so every other
  precondition passes, with the SPARE producer's **real** session rather than
  a stand-in; `("refused","capability")`, and the real ending still finished.
- **an interrupted write recovers** — one synthetic `OSError` from
  `ControlStore.transact` for the first `review-line.release-writer` operation
  and nothing else, modelled as a process death because the serving loop does
  not catch it. The fixture keeps the aborted run's stores and ticks again with
  nothing patched: the line ends `idle`, the writer `revoked`/`released`, there
  is **exactly one** journalled `attempt.finalize-quiescent` (no second
  Authority fence), and the Work's gate is discharged.

Runs, with full provenance in `evidence/claim-365537/HOW-THESE-WERE-RUN.txt`:

- **`tests.tools.test_fresh_retry_line_recovery`: 25 OK.**
- **`tests.tools.test_retry_task_lineage`: 24 OK.**
- **Whole `tests/job_manager`: 1375 OK.**
- **The five non-version-control tools suites: 164 OK.**
- **Both reviewer probe scripts re-run unchanged**, outputs kept in
  `evidence/claim-365537/probes/`: `completed_probe.py` now refuses with the
  line still `writing`; `replay_probe.py` now answers the committed document.

### The version-control gap is closed here, not transferred

The review states the reviewer shares the Git restriction and that connected
deterministic evidence may establish reader behaviour. So the two
`tools/stage_execution.py` readers changed at claim365155 are established by
connected evidence rather than referred onward:

- `_fenced_gate` — the discharge is read through
  `worker_manager.gate_discharge_of` and the Work's gate through
  `Authority.project_work`, in the lineage suite and again in the
  interrupted-write case.
- `_fence_operation` — the one-producer case's refusal NAMES the review route,
  which exists only because the released ending's handoff was fenced by an
  authority operation that reader had to find. A released ending carrying none
  would never have moved the Work to `rview`. Recorded in that case's own
  words.

My previous claim's PROGRESS and handoff said those classes were the
reviewer's to run. That was wrong, and this entry supersedes it without
rewriting it.

### Cost

Reading both reviewer probes, `output._provable` and `output.frozen_output_of`,
`schema.DISPOSITIONS`, `_quiescent_completed`, and `_frozen_checkpoint`'s
mutable-pointer correction. Test runs: the recovery suite six times (three
failing — a fixture reaching for a composition it had not yet captured, and
twice an `OSError` escaping a loop that does not catch it, which is what made
the interruption model honest), the lineage suite twice, `tests/job_manager`
twice, the five-suite group once, and both reviewer probes twice each. No live
provider, no container engine, no network, no credential, no deployed-instance
mutation, no version-control operation.

### Boundaries

No version-control operation of any kind. The canonical `v12/python` tree is
byte-unchanged. `candidate-365081` and `candidate-365155` and their evidence,
and this dossier's `FINDING.md`, `PLAN.md` and reviews, are untouched; I wrote
`candidate-365537/`, `evidence/claim-365537/` and this file. The reviewer's
reproduction was not weakened — both probe scripts run unchanged and are kept
as this claim's own evidence. `grant_writer` was not broadened, no verdict was
manufactured, nothing offered for review was reopened, and no
unresolved-runtime hold was cleared by hand.
