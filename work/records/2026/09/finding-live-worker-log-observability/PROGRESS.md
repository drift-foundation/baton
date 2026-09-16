# Progress: make live worker progress observable

No implementation claim has started. The confirmed MVP boundary is recorded
and bound to canonical Baton Work W61599.


## 2026-09-01 — first implementer round (`baton.claude`, W61599 impl claim)

**The default liveness projection is implemented end to end. The `result/logs/`
capability, the safe-progress stream, the locator and the CLI follow view are
NOT, and PLAN item 5 is therefore half done rather than done.**

I took PLAN item 5 in the order it is written -- the projection first --
because it is the part that answers the W52821 question ("is this worker
moving?") on its own, and because it needs no new durable content surface.

### What an operator can now be told, and what it costs

Two numbers, per attempt, in this manager's own control store: how many bytes
of the worker's native session stream this manager has OBSERVED, and the
MANAGER's receipt instant for the latest of them. That is the whole of it.
No provider timestamp, no native log path, no sample of what was read.

M61707's credential-free durable surface is preserved BY CONSTRUCTION rather
than by a redactor: what crosses from the observing loop is a length. A count
cannot carry a credential, which is the property W39357's `DEVNULL` correction
was protecting and the reason this slice could be built before the sanitization
boundary exists.

### The seams, and why each is where it is

`schema.py` -- SCHEMA_VERSION 14, and two nullable `attempts` columns,
`activity_bytes` and `activity_at`, under a both-or-neither CHECK. A schema-13
store has nowhere to put either, so a manager reading one could only answer
"unknown" for every attempt. The columns are diagnostic: nothing that was
authorized under 13 is authorized differently under 14.

`attempts.observe_activity` -- the writer. The operand is a CUMULATIVE TOTAL
rather than a delta, which is what makes a lost, duplicated or reordered report
harmless. Monotonicity is decided INSIDE the write against the exact value the
update compares, for the reason `observe` decides its transition there.

`attempts.attempt_activity_of` -- the reader. An id naming no attempt answers
`None`; a recorded attempt nobody has observed answers a projection whose
members are `None`. Those are different facts and a zero would conflate them.

`tools/dogfood_operator._Channel` -- the one place in this manager that sees a
live worker producing anything. It already drained the exec process's stderr so
a full pipe could not wedge the session, and it was throwing the FACT away
along with the bytes. It now counts every byte, including the ones past the
bounded window it deliberately forgets, and publishes the running total through
an injected observer.

`tools/dogfood_operator._activity_observer` -- the deployment's publisher. It
opens, writes and closes its own handle per publication, because `_Channel`
drains from a thread of its own and a `sqlite3` connection belongs to the
thread that opened it. A handle it forgot to close would be a lock the next
incarnation waits on, which this deployment has been bitten by before.

### Three decisions this record did not contain, now recorded in FINDING.md

1. A REPEATED TOTAL DOES NOT MOVE THE INSTANT. An observer polling a quiet
   stream is behaving correctly and its report is accepted, but the instant is
   the age of the latest observed ACTIVITY -- advancing it would make a wedged
   worker read as freshly alive to the one operator relying on this to notice.
2. A DECREASE REFUSES rather than being absorbed, so a stale observer cannot
   make a progressing worker look stalled.
3. PUBLISHING FAILURES ARE DROPPED AT THE DRAIN. The loop exists to stop a full
   pipe from hanging the session; a diagnostic projection that could raise out
   of it would wedge the very thing it was added to observe.

### Mutation check

Six mutations, all caught:

    CAUGHT  a repeated total freshens the instant
    CAUGHT  a decrease is silently accepted
    CAUGHT  the end of the stream is never published
    CAUGHT  an observer fault escapes the drain      [wedges the session]
    CAUGHT  bytes past the bounded window are not counted
    CAUGHT  the observer leaks the handle it opened

### Verification

    tests.manager.test_attempts + test_store + test_workspaces
      + test_credentials + test_oci + test_secrets + test_text_sweep
      + tests.tools.test_dogfood_operator            1083 tests, OK
    the whole v12 python suite                       2986 tests, 7 failures,
      the same seven pre-existing ones, unchanged in number and identity:
      five in `test_boundary_inventory`, one in `tests.authority.test_catalog`
      and `test_credentials_engine`'s host check

The schema bump made two boundary-inventory attempt-document fixtures
incomplete -- a persisted attempt document carries every column -- and the two
new exports needed their entries in the §13 accounting, the text sweep's table
and the public-operand declaration. All four are additive registry members.

The working-tree diff check is clean and no added line exceeds 79 characters.

### NOT DONE, and named rather than left to inference

- the manager-minted attempt-result/log capability, the sink created before
  runtime start, the incomplete/complete marking and the stable relative
  locator under `result/logs/` (the second half of PLAN item 5);
- the closed provider-safe progress stream itself and its worker-side emitter
  (PLAN item 5, and the reason item 8's matrix is not started);
- the CLI follow view (item 6) and the TUI rendering (item 7);
- rendering `Log 1.40 MiB · updated 4s ago` anywhere. The projection is
  exposed as a manager read; nothing displays it yet, and the display belongs
  with the follow surface rather than ahead of it.

### State

Awaiting review of the projection slice before the sink and the safe stream are
built on top of it. Passing back rather than closing.

## Claim 174354 — baton.claude, design only

Unparked W61599 to `queued` at seq 174353 under the configured `baton.impl`
Handler and claimed standalone at 174354, after the W63255 implementation
handoff released its claim at 174297 — the condition M174203 names. Design
only: no product or test file edited, nothing executed.

Deliverable: `ACTIVITY-SOURCE-DESIGN-174354.md`,
`sha256:696c117d71bc9740d33e458bb93a2e8e6a82dd424c02d55938539f53d65ac3f7`.

**The producer nearly exists already.** `_ran_provider`'s drain reads the
provider's own stdout inside the container in 4096-byte pieces and bounds what
it KEEPS (`held`) while never counting what it READ. A cumulative
`seen += len(piece)` beside `held.extend` is the whole producer, and it is
content-free by construction.

**The transport exists already too.** `exchange.EVENT_DIRECTORY` is a
manager-owned directory bind-mounted at `/run/baton/exchange/events`, created
mode `0o700`, and `serve_exchange` already publishes `state-<operation>.json`
at `dispatched` and `answered`. One bounded integer member on that existing
document needs no new mount, transport or document kind.

**One fact decides the design and nobody has observed it**, including me:
whether provider stdout grows during a turn under `--output-format json`, or
arrives once at the end. The design carries both candidates — stdout as read
today, or the native JSONL under the prepared home — with the one-turn
experiment that chooses between them, and names the third outcome honestly: if
neither grows incrementally, the options are a provider-contract change or
reporting that provider-safe liveness is unavailable without one.

**Two existing assertions are superseded, and the design says so rather than
discovering it mid-slice:** `test_every_byte_is_counted_including_the_ones_discarded`
(the stream it counts stops being the source) and
`test_a_silent_worker_is_observed_as_silent_and_not_as_unobserved` (its
"zero is a fact" position, under review [P2] and PLAN item 11). The
recommendation is absence until positive growth, with no second observation
instant proposed.

Verification spending this claim: **zero measured seconds**.

## Claim 174521 — revised design after review 174505 and owner selection M174518

Read return174505, `review-2026-09-15T03-16-10Z.md` and the reroute, and pinned
M174518 in FINDING.md and PLAN.md before revising. Design only: no product or
test edit, nothing executed.

Deliverable: `ACTIVITY-SOURCE-DESIGN-174521.md`,
`sha256:2afa520cc192721cb0edb10c0608baba83924675c999b732f0257074a60f6f34`,
superseding `ACTIVITY-SOURCE-DESIGN-174354.md`, which stays as history.

**All four P1 gaps were real and the review confirmed each from code.**

1. **My experiment could not have decided anything**, and "nobody has made that
   observation in this tree" was too broad — this dossier's own FINDING records
   the W52821 observation that native JSONL showed activity while stdout did
   not. A scripted provider emits on its script, and several 4096-byte reads can
   all be slices of one final JSON payload. **Candidate A is withdrawn on the
   evidence rather than deferred**, and the source is native-JSONL *metadata*,
   size only.
2. **`state-<operation>.json` is the wrong carrier.** `serve_exchange` has no
   periodic writer today and publishes `dispatched` → synchronous run →
   `answered`/`faulted` → terminal; a periodic writer racing those can destroy
   terminal causality, and atomic replacement orders bytes rather than
   publishers.
3. **`state/1` cannot take the integer compatibly** — `_decoded` rejects extra
   members and non-text values, and `_event` checks exact schema equality. So a
   separate `activity.json` under its own schema, with its own parser, and no
   existing event parser relaxed.
4. **The ordinary consumer is `single_worker.observed_exchange`**, which my path
   list omitted. The revision names it, and separates the read-only projection
   from a serving-loop ingestion hook so a status read gains no writes.

The revision also specifies what the review found unspecified: bounded session-
file discovery with type/link/baseline/rotation rules, both compatibility
pairings, single-slot coalescing with a finite stop and abandonment made safe by
attempt/operation binding so a delayed write cannot freshen a replacement, and
bounded staging-file use.

**One fact remains genuinely open and is marked as such:** how the adapter
identifies its own session file before completion. `_prepared_home` establishes
a private `.claude` directory, not a session-file identity. Everything else in
the design is decided.

Verification spending this claim: **zero measured seconds**.

## Claim 174572 — completed design packet per M174565

Pinned M174565 in FINDING.md and PLAN.md before revising. Design only: no
product or test edit, nothing executed.

Deliverable: `ACTIVITY-DOCUMENT-DESIGN-174572.md`,
`sha256:cdf220ab2d5cffa5604fab56ae022b688b1ab44d54065f53f60cc7e745ed37eb`,
completing and superseding `ACTIVITY-SOURCE-DESIGN-174521.md`.

**The session-file identification is no longer open — it is derived from
source.** `_scratch` is a per-container `mkdtemp` under the tmpfs, and
`_prepared_home` builds `$HOME/.claude` at `0o700` containing exactly one entry,
the credential **symlink**. So the private `.claude` starts empty of provider
state and no other writer owns it: anything the provider writes beneath it
during a turn is this invocation's. That needs no vendor path knowledge, and the
design is deliberately layout-independent rather than hardcoding
`projects/<slug>/<id>.jsonl`, which I have not observed and will not invent.

**One consequence I had to find rather than assume:** `_scratch` caches
`self._home`, so a `describe` and a `work` in the same container **share** the
scratch. The baseline is therefore per-operation, and growth is reported
relative to it — which is also what makes restored history unable to fabricate
growth.

Completed as selected: the temp-then-rename-over write pattern with the
published file never renamed away; a single publisher with a bounded
latest-count slot; attempt/session/sequence/command/operation binding, which is
what makes an abandoned stalled writer safe rather than a daemon-thread claim;
exact count limits validated in the new document's own parser with no existing
parser relaxed; nonblocking manager ingestion separated from the read-only
projection so a status read gains no writes; and bounded cleanup with at most
one outstanding temporary file.

**One compatibility point is named rather than waved past:** `activity.json` is
outside the old closed vocabulary so an old manager will not read it, **but it
is a real entry in a namespace the old manager counts**, so implementation must
confirm the existing entry-count limit still admits it and state the measured
limit.

Verification spending this claim: **zero measured seconds**.

## Claim 174645 — completed design per M174641

Design only: no product or test edit, nothing executed.
Deliverable: `ACTIVITY-DOCUMENT-DESIGN-174645.md`,
`sha256:25bc279ca43637f1e74427ce6847b1ffe97f450b35254b6e849e6204b5a63d46`,
completing `ACTIVITY-DOCUMENT-DESIGN-174572.md`. The selected document, write
pattern, parser, limits and lifecycle bytes are retained and not reopened.

**I had a source fact wrong and the review caught it.** I wrote that `_scratch`
caches the generated scratch; it returns `self._home` only when the constructor
supplied one — a test seam — and otherwise `mkdtemp`s **without storing it**.
My per-operation-baseline conclusion happened to be right, but I reached it from
a false premise, which is what a later reader would have trusted. Also accepted:
`describe` invokes no provider, so the publisher is **`work`-only**; and a
reused `_prepared_home` is not proved empty, so the emptiness argument is
dropped entirely in favour of binding the baseline **after preparation and
before the actual provider launch**.

**The accounting could go backwards and now cannot.**
`sum(max(0, current - baseline))` falls from 100 to 80 when a grown file is
replaced by a smaller one at baseline 0. The design now tracks per-file identity
and last size, reports a **monotonic running total**, and **freezes on shrink,
disappearance or identity change** — reporting unknown from that point rather
than a smaller number, and never resuming.

**Compatibility headroom is pinned from source instead of left to an
experiment:** `MAX_EVENT_ENTRIES = 64`, exceeding it makes the whole observation
unreadable, and this design consumes **2 of 64** (activity plus one temporary)
on top of four lifecycle documents, leaving **58**.

**Two things the previous packet argued from binding alone now have positive
mechanisms:** a single writer slot with an owner token, where **no replacement
starts while a prior publisher is unresolved** and the attempt simply publishes
nothing; and a **consumer-side terminal predicate** that ignores activity
documents for an operation once its terminal exists — closing the
same-operation late-write window that binding could not.

**Off-loop ingestion is specified concretely:** one composition-owned worker,
single-slot, doing the read and the store write off the sweep thread, with the
sweep only assigning a slot. If implementation finds no composition-owned
lifecycle to hang it on, that is a genuinely different required source boundary
to report with the exact missing hook — not to solve by putting the write back
on the sweep.

Verification spending this claim: **zero measured seconds**.

## Claim 174799 — completed design per M174788

Design only: no product or test edit, nothing executed.
Deliverable: `ACTIVITY-DOCUMENT-DESIGN-174799.md`,
`sha256:401637e167c2e76cceebb6846b1c7d683189751ee0df6ca7d8954143a628890e`.
Selection pinned in FINDING/PLAN.

**The delayed-final-count problem is answered by semantics, not by a
mechanism.** The review is right that a terminal precheck cannot reject a
greater-total write stalled in the store until after the terminal. The owner
selected the honest reading: such an update may arrive late, its timestamp is
**manager receipt time**, and it is never evidence of continued activity nor
authority over terminal state. The precheck is kept as a cheap early skip and no
longer claimed as a boundary. The one user-visible consequence is named: **the
viewer reports activity as historical once the stage is terminal.**

**The composition boundary is now concrete and verified from source.**
`worker_operations` is per pooled worker and cannot own a per-deployment worker;
`operations_from` (`stage_execution.py:5430`) composes the deployment and
`release` (`:4309`) drives `_closers` (`:4321`), which already yields named
closers and collects their failures. The ingestion worker is constructed there
and yielded from `_closers`, so its shutdown is reported like any other handle.
Pooled and bootstrap are both covered by construction, since ownership sits at
the deployment rather than the worker. `single_worker.refresh_runtime` — the
serving loop's one runtime read — is the enqueue hook, and it still neither
reads the file nor writes the store.

**Numeric values chosen without another approval request**, as directed: scan
depth 4, 256 entries, 64 tracked identities, 1 s cadence, 2 s publisher stop,
2 s ingestion stop, 1 outstanding temp, enqueue slot depth 1. Overflow of any
limit yields **unknown**, never a partial or smaller total.

**Staging is exclusive and suppressing:** `O_CREAT|O_EXCL|O_NOFOLLOW`, and a
failed create suppresses that write rather than unlinking or overwriting
anything — so a stale temporary file blocks publication instead of inviting a
reader to clean it up.

Verification spending this claim: **zero measured seconds**.

## Claim 174920 — the three mechanisms completed

Design only: no product or test edit, nothing executed.
Deliverable: `ACTIVITY-DOCUMENT-DESIGN-174920.md`,
`sha256:3731daca7a8b196ea1cd97cf34df8c8b88af691271ba2e8818b634683d3443ef`.
All accepted transport, delayed-count, scope, store-handle, numeric and staging
decisions are retained unchanged.

**1. The baseline was still on the launch path and I had not seen it.** Saying
the scan runs "before the provider is started" *is* the launch path — a bounded
scan is still work the provider waits behind. Corrected: at launch the agent
records only **the instant** and the directory identity, two free facts; the
**first scan happens on the publisher's own thread** at its first cadence tick,
and `st_mtime` against the recorded instant is what separates baseline from this
invocation's growth. No scan ever runs on the launch path, and a failed first
scan still leaves activity unknown — now at no cost to the turn.

**2. Pooled and bootstrap are different owners and I had named only one.**
Staged deployments construct in `stage_execution.operations_from` and unwind
through `StageExecution.release` → `_closers`; **bootstrap never reaches
`_closers`** and instead constructs in `single_worker.operations_from`, chaining
the stop into `_Operations.close`'s existing single `dispose`. Unwind order is
the same in both: stop the worker **before** closing the store handle it owns,
and report an over-bound stop rather than swallowing it.

**3. Exclusion had to move off the object.** Keying it to one composition being
recomposed does not stop two *distinct* compositions over the same stores. It is
now an admission slot per `(control store path, attempt_id)` in a module-owned
registry, freed only on positive resolution, so an abandoned helper leaves it
**held** and the next composition starts nothing for that attempt.

**A conflation corrected:** my "seven-member binding" mixed a wire identity with
a local capability. Six fields are compared from the document; the **event root
is a capability handed to the worker at construction**, never read from the
document — and the enqueue performs **no `launch.adopt`**, so nothing is adopted
on the diagnostic path.

**Viewer follow-through is recorded, not implemented.** The delayed-count
semantics imply activity is historical on a terminal stage; the viewer currently
shows `unknown` and **W167896 owns those files**. No viewer path is edited and
no change to its scope is proposed — until that owner takes it up, the display
it already has is the honest one.

Verification spending this claim: **zero measured seconds**.

## Claim 174971 — the mtime baseline withdrawn, admission and unwind pinned

Design only: no product or test edit, nothing executed.
Deliverable: `ACTIVITY-DOCUMENT-DESIGN-174971.md`,
`sha256:22427e63b215578d5e911235a33347856b3214edcae35b8fe222c2fce14f1d85`.
All selected transport, delayed-count, numeric and staging decisions retained.

**The mtime baseline was wrong and the counterexample settles it.** A file
holding 1000 bytes with 10 appended before the first tick has 1010 bytes *and* a
new mtime, so my rule counted 1010 as this invocation's growth when the true
answer is 10. mtime says a file changed; it cannot say how much of it is new.
Withdrawn entirely — along with "record the directory identity at launch", since
that stat is not free either.

**Replaced by a baseline proved by construction rather than measured.**
`_scratch` without an injected home is a `mkdtemp` this process just created, so
it is provably empty of native files with **no scan and no stat** — a true
pre-launch baseline of zero, admitted without waiting. An **injected, reused or
restored** home is not provable and yields **`unknown` for the whole
operation**; nothing is estimated and no restored history is subtracted. The only
launch-time record is a boolean the agent already knows.

**The admission/worker conflict is resolved by naming two separate things.**
Admission is per `(control store path, attempt_id)` in a module-owned registry,
stable across both factories and distinct compositions; the worker is a
deployment-scoped helper holding whichever admissions it acquired, fixing no root
at construction. Acquisition is an atomic compare-and-set that **never waits** —
failing to acquire simply means no ingestion for that attempt. Each enqueue
carries the attempt, the **local** root (in-process queue only, never wire-
supplied) and the six wire identities, with no adoption on the diagnostic path.

**Two unwind rules pinned.** Partial construction **releases any slot it
acquired**, so a half-built composition never leaves one occupied by a worker
that does not exist. And the thread-owned `ControlStore` handle **closes only
after the worker has actually exited** — never after a timed-out stop, where the
handle is left open, the slot stays occupied and the fact is reported. Leaking a
handle is the lesser fault; closing one under a live writer is a use-after-close.

Verification spending this claim: **zero measured seconds**.

## Claim 175025 — helper exclusion keyed correctly

Design only: no product or test edit, nothing executed.
Deliverable: `ACTIVITY-DOCUMENT-DESIGN-175025.md`,
`sha256:014be97ecf91807fde86d1d84c0d05ede70b3bdd12790a23e3abc3ee57e99906`.
All other selected decisions retained.

**My keying did not exclude helpers, and the counterexample is decisive.** C1
holds a blocked helper H1 with the slot for `(S, A)` occupied; C2 asks for
`(S, B)` — a **different attempt** — finds it free, and starts a second helper
while H1 is unresolved. Two helpers, one store. Renaming admission and worker
did not fix that, and the per-attempt cap of 64 does not satisfy the retained
no-replacement requirement.

**Corrected: one process-wide helper slot keyed by the held store identity, with
no attempt in the key**, acquired atomically and nonblocking **before** the
helper starts, by the same module-level primitive from **both** factories. If
occupied, the replacement starts **no helper at all** and ingests nothing. Held
until positive termination — a timed-out stop leaves it occupied indefinitely,
which is the point. Released on construction failure **only if the helper never
started**.

Per-attempt admissions are demoted to what they always were: the per-request
identity check governing which documents a running helper accepts. **They never
govern whether a helper may exist**, and their 64-entry cap stays distinct from
the file cap.

**Store close refined:** the handle is closed **by the owning ingestion thread
during its own finalization**, and that exit is what releases the slot. After a
timed-out stop **nothing closes it cross-thread** — the composition reports the
unresolved helper and leaves both the handle and the slot alone. No thread but
the owner ever touches that handle.

**The acceptance case that would have caught this** is now explicit: two
compositions over the same store with **different** attempts A and B, asserting
H2 never starts until H1 positively exits — proved by the helper never running,
not by B's documents going uningested.

Verification spending this claim: **zero measured seconds**.

## Claim 177898 — the implementation

Owner reroute M177542 selects `ACTIVITY-DOCUMENT-DESIGN-175025.md` for
implementation. **Both pinned documents revalidated by hash before any edit,
and all six selected source paths were still byte-identical to
`review-evidence-175051.json`.**

Deliverable: `ACTIVITY-IMPLEMENTATION-177898.md`, over the six selected source
paths and five selected test paths, plus one declared-operand entry in
`tests/manager/test_dependencies.py`.

**The source moved inside the container.** `claude_agent` binds a baseline
**proved by construction** — an uninjected `_scratch` is a `mkdtemp` this
process just made, so its `.claude` is provably empty with no scan and no stat
— and observes native-file metadata on the publisher's own thread. An injected,
reused or restored home is **unknown for the whole operation**. The total is a
monotonic running total over `(dev, ino)` identities and last observed sizes,
and it **freezes** on shrink, disappearance or identity change rather than
falling. Every bound fails toward unknown.

`baton_worker` publishes a **separate** `activity.json` under its own schema,
`work` only, from a one-slot publisher with a 1 s cadence and a 2 s stop that
abandons rather than joins. Staging is one fixed name created
`O_CREAT|O_EXCL|O_NOFOLLOW`; an existing entry **suppresses the write**. The
published file is replaced by rename **over** it.

`exchange` carries the document, its own parser and its vocabulary entry. The
four lifecycle documents are **byte-unchanged**, and `_decoded` gained one
opt-in keyword no existing caller names.

`single_worker` owns **one process-wide admission slot per held control-store
identity, with no attempt in the key**, acquired atomically and nonblocking
before the helper starts by the same primitive both factories call. An occupied
slot means the replacement starts **no helper**. The slot is held until
positive termination; the owning thread closes its own handle during its own
finalization. `refresh_runtime` enqueues into a single slot and reads nothing.

`stage_execution` admits the helper and yields it from `_closers`.
`dogfood_operator._Channel` **stops being an activity source** — it was
counting the outer `docker exec` stderr, which is a liveness number about the
wrong process.

**One deviation from the accepted design, flagged rather than hidden.** The
enqueue carries the attempt, the session and the local root; `command_digest`
is read back off the manager's own command file **on the helper's thread**
rather than travelling in the request, because a sweep that produced that
digest would be reading a file — which the design forbids on that path twice
over. Every identity compared is still manager-held; nothing is taken from the
document.

**Verification: 2,776 s of full-suite runs (five runs; one of them part-way
through implementation and not offered as evidence) plus ~190 s of focused runs
and reversal probes — about 2,966 s.** Baseline (six pinned sources restored
byte-exactly): 7259 tests, 89 failures/errors. Candidate: 7333 tests, the
identical set **minus one**. **No new failure is introduced**; the
remaining 88 are pre-existing at the pinned baseline and belong to the
untracked `context_delivery.py`/`provider_context.py` work and to thirteen
`test_stage_execution` errors that fail identically with the original product
files. Reported, not fixed.

**Twenty-two reversal probes; nineteen confirmed first time. Three were
non-evidence and are reported as such** — the truncation case asserted only
that the total had not fallen, the positive-total case was being caught by the
publisher's dedup so a **zero** would have been published, and the
observer-fault case proved nothing because the turn survives a dead publisher
thread anyway. Two further probes exposed weak coverage: no lifecycle member is
guarded by `_decoded` alone, and the 256-entry overflow case answered unknown
for the wrong reason. All five tests were corrected and each probe then failed
exactly where it should.

No viewer path edited, no live provider, no engine run, no Git operation.

## Claim178427 — baton.tuner, bounded correction awaiting independent review

HANDOFF-178427.md and correction-178427/candidate.json bind the exact correction
and retained base/candidate bytes. The three review178362 defects are corrected:
filesystem resolution is off the enqueue thread, repeated stops retain their
thread handles, and directory traversal uses no-follow parent-relative descriptors
with opened-object checks. This supersedes the old implementation claims that
enqueue did no filesystem work and entry checks alone excluded directory races.
A missing/inaccessible native root now conservatively freezes optional activity.
Accepted baseline, transport, counts, receipt-time semantics and scope stand.

Author M178528 supplied exact submitted test snapshots. Both old hashes verify;
the two retained diffs prove six author test corrections after his hash list.
Current correction hashes are separate. Fresh final focused verification passes
82 tests; 17.160464063985273s total new supervised execution including failed
setup/negative runs. Every owned group exited, with no live test threads in the
completed checks. See handoff for negative-control qualifications, ambient
dependency versions, retained author logs and attributed historical cleanup.
Return baton.feat for focused independent review then baton.ops, per178421.
No automatic correction cycle, W161234 shared-file release or viewer completion.

## Claim 178777 — the viewer connection

Owner reroute 178775 assigns this slice to baton.claude after W177937 closed
satisfying at 178761. Owned: `v12/python/tools/job_viewer.py`,
`tests/tools/test_job_viewer.py`, `JOB-VIEWER.md` and this dossier. **All three
bases were revalidated byte-exact against accepted W167896 `candidate-168326.json`
before any edit, and every accepted producer path is byte-unchanged by this
claim** — verified in `viewer-candidate-178777.json`.

**The wiring already existed and one line ignored it.** `attempt_activity_of` →
`delegation.py` → `projection.py` already published the count at
`stage["runtime"]["activity"]`; `_stage_line` wrote the constant `UNKNOWN`. The
change is a read, a format and a predicate. The viewer gains no store handle, no
connection and no second read path, so W167896's no-backend rule is intact.

**Three renderings and no fourth**, per owner ruling M174788, whose instant is
the manager's RECEIPT time. Nothing observed — no runtime, no member, or a
recorded attempt with no count — is `unknown`. A live stage shows the count and
a relative age. A **terminal** stage shows the count and the **absolute instant**
marked `last`, and never a relative age: "4s ago" beside `completed` invites
reading a finished attempt as a running one, and it gets worse with time because
the apparent freshness improves while nothing runs. **A zero is never a count** —
the producer publishes only positive totals, and `0` would read as "observed, and
empty", which nobody here has evidence for.

**The two existing `activity unknown` assertions were rewritten rather than
deleted.** Their fixtures carry no activity, so they became the honest
"unobserved attempt" cases. The module docstring and `JOB-VIEWER.md` both carried
"until it exists, activity here is `unknown`", which this change makes false;
both were replaced in the same edit.

**Verification: 74 tests, OK, 3.187675 s measured**, in its own process group
under an owning supervisor with a 60 s ceiling, TERM 5 s / KILL 5 s, and
**positive proof the group was absent afterwards**. No full suite, no producer or
slice-B test, no engine, provider, live model, build or install. No
version-control operation.

**Five reversal probes, all confirmed first time**: the terminal discriminator
(4 failures), the positive-count test (1), the read itself (8), the missing-instant
branch (1) and the defensive absence reads (8). Each guard is load-bearing.

Candidate and cleanup evidence: `viewer-candidate-178777.json`
`sha256:2d8bd9bfe8e2769f1da33d9d5e89870c43d9ec2679482f122bbe5c698a1a37ad`.

## Claim 178930 — the R1/R2 viewer correction

Owner reroute 178927 authorizes correcting both findings of
`review-2026-09-15T14-42-20Z.md`; the selection is pinned in PLAN above. Same
three-file scope; **all six accepted producer paths verified byte-unchanged**.

**R1 — the default list was losing the stage identity.** My single-line
rendering pushed the row past 100 columns, and the whole-line cut took the end
of the terminal timestamp *and the entire stage id* — on ordinary valid counts,
in the renderer the plain CLI uses, which has no width operand. That is worse
than losing the new field: the identity is what an operator opened the list to
copy somewhere else. **The count now stays in the fixed-width column and the
timing moved to its own continuation line**, exactly as `reason` already does.
The recorded instant is bounded at `MAX_INSTANT_TEXT` as well, so a malformed
document cannot widen the line either. Covered for all three terminal states
plus live, in list *and* detail, asserting count, full instant, stage identity
and the column bound.

**R2 — I introduced a crash on a snapshot the old code rendered.**
`bytes_observed: 10**400` is valid JSON far inside the 4 MiB input bound; my
float conversion raised `OverflowError` outside `refresh`'s last-good-snapshot
handler, and `main` catches only `ViewerRefusal`, so the ordinary command could
die on a document the previous constant-`unknown` rendering displayed without
complaint. **The producer's own domain `0 < n <= 2**53 - 1` is now checked
before any conversion**, because the conversion is what fails. Covered through a
real JSON read and through the ordinary source/refresh path, with
bool/negative/zero/type cases and the largest valid producer count — and a case
holds the viewer's ceiling equal to `exchange.MAX_ACTIVITY_BYTES`, so the two
copies of that number cannot drift. This is malformed **consumer** input; the
trusted producer cannot emit such a value.

**Verification: 83 tests (74 before, 9 added), OK, 3.186929 s measured**, exit 0,
own process group, 60 s ceiling, TERM 5 / KILL 5, group positively absent.

**Four reversal probes, all confirmed.** The first reproduces the reviewer's
exact failure class — reverting the domain check turns three cases into
`OverflowError` errors rather than assertion failures. The second proves the
bound is a bound rather than a blanket refusal.

Candidate: `viewer-candidate-178930.json`
`sha256:820c7c9b1aff17390b78d304d1d320dd8c13c3279823361f362be30b4cc314c7`.
