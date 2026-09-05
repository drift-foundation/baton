# Progress

2026-09-04 — `baton.prompt` created the missing bound dossier from the
measured production-bootstrap failure. No implementation has started.

## 2026-09-04 — baton.claude (impl), W83781 claim

Plan items 1–7 implemented. Every pinned decision was revalidated against the
current tree first: `episodes.identities` still hashed only `stage_id` and
`episode`, `JobStore.open` still took only a path, an incarnation and a clock,
`meta` still held only `store_kind` and `schema_version`, and
`operations_from` still opened with `del job_store`. The reviewer's baselines
reproduce exactly: 246 Job Manager tests and 71 production-composition tests
pass on the tree as found.

### What was built

**The binding.** `JobStore.open` requires an Authority UUID, proved before the
path is opened at all, persisted in `meta`, and exposed as
`store.authority_uuid`. A new store writes it in the same transaction as the
kind and version; schema-1 and schema-2 stores are pinned in the same
transaction that stamps schema 3, so a failure rolls the UUID and the version
back together. A later open naming another Authority refuses and the file is
byte-for-byte unchanged.

The rule is the Authority package's own `check_authority_uuid`, imported
rather than restated, with the refusal translated to this package's
`ContractRefusal` — `schema.check_authority` owns that one translation. A
second, looser spelling of "32 lowercase hex" in the Job manager is exactly
the drift the finding forbids, and importing a predicate is not importing an
Authority: it opens nothing, holds nothing and grants nothing.

**The derivation.** `identities(authority_uuid, stage_id, episode)` hashes the
canonical triple and keeps the `offer-`/`attempt-` spelling over one shared
digest. Both `open_first` and `open_next` take the namespace from
`store.authority_uuid`, which is why the binding lives on the store rather
than arriving through the deployment factory: `open_first` runs inside
`submit`, before any factory exists, so a factory-threaded namespace would
arrive too late for episode 1 and the two paths would derive from different
inputs.

**The operands.** `--authority-uuid` is required on `submit`, `status` and
`serve`. `status` still constructs no Authority and holds no session; it names
one. `operations_from` compares the store's binding with the configured UUID
**before** configuring the workspace group or storage, certifying a profile,
allocating anything or opening the Authority — the ordering is the correction,
because every one of those writes.

### Verification

- 266 Job Manager tests (246 before) and 74 production-composition tests (71
  before) pass. Whole tree 3707 with the same eight failures that reproduce
  without this candidate.
- New evidence: same-authority replay across several episodes; two authorities
  never deriving one identity, from the measured stage name; the shared digest
  behind both spellings; the namespace unaffected by incarnation; malformed
  authorities refused at the derivation and refused before a store path is
  created; a new store persisting its binding; a same-UUID reopen; a
  different-UUID open refused byte-for-byte; schema-1 and schema-2 migrations
  pinning atomically while keeping every identity and receipt; the namespace
  applying only to an episode opened after the migration; a legacy store
  pinned to whichever Authority opened it; the production preflight refusing a
  mismatch and leaving the control store unconfigured with no engine call; and
  the OCI half — the foreign-authority container still refused, and a
  correctly namespaced fresh attempt selecting nothing of the stranger's.
- `tests/manager/test_oci.py`'s existing whole-label comparison is untouched.
  It is the negative control this correction must not weaken: a build that
  started selecting containers by attempt id alone would make the collision
  silent instead of fixing it.

### The W81857 overlap, and how it resolved

Seven of the paths this plan schedules were also bound by W81857's
then-unintegrated proposal: `tools/single_worker.py`, `DEPLOYMENT.md`,
`tests/job_manager/{fixtures,test_status,test_launch,test_tool}.py` and
`tests/tools/test_single_worker.py`. While that was true this candidate was
being prepared as a STACKED proposal, declaring W81857's digest as a
prerequisite and diffing against base-plus-prerequisite, so that its patch
would carry only its own changes and the two would integrate in a stated
order.

**That is no longer necessary.** `756b720 feat(v12): drive workers through
durable file exchange` integrated W81857 while this Work was being
implemented, and `389cdd4` followed it. The declared base for this proposal is
`389cdd4`, which already contains the file exchange, and the working tree
holds exactly this Work's own changes on top of it — checked mechanically:
every dirty path is one of this candidate's seventeen source paths or one of
its three record files, and nothing else is dirty. There is no stacking, no
prerequisite, and no overlap left to sequence.

The suite numbers above were measured on that base, so they already include
W81857's tests.

## 2026-09-04 — baton.claude — response to review-2026-09-04T09-07-42Z

One P0, two P1s and two P2s, all five reproduced and corrected. The P0 is
recorded as a decision in `FINDING.md`; it corrected the implementation rather
than the boundary.

- **The migration now decides under its own lock.** The version is re-read
  after `BEGIN IMMEDIATE`, a waiter that finds the store already migrated
  writes nothing and returns, and the binding is stamped with a plain
  `INSERT` — replacement semantics are wrong for a value that is immutable
  once written.
- **The persisted binding is owned as an Authority before it is compared**, so
  a corrupt row is `integrity/schema` rather than a valid store belonging to
  somebody who does not exist.
- **The rollback vector exists**, driven through the public `JobStore.open`
  boundary with a failure injected while the migration transaction is open.
- **The OCI vector now calls `start`** against an engine that retains the
  other Authority's container and honours the attempt-id selector, and asserts
  exactly one `run`.
- **Both direct-run guards moved to the end of their files**, so
  `python3 tests/job_manager/test_store.py` and its sibling exercise the cases
  this Work added rather than exiting above them. Checked by running both
  files directly: 42 and 22 cases.

Replayed against the reviewed digest with only the two changed test files
substituted: two failures — the stale-opener rebind and the corrupt binding.
The rollback and the one-`run` vectors PASS there, and are reported as
coverage the review found promised-but-missing rather than as regressions: a
case that passes on the digest it was written for is not one.

## 2026-09-04 — baton.claude — response to review-2026-09-04T09-22-40Z

The source behaviour this review accepted is unchanged. Both remaining items
are about what the two migration regressions actually measure.

- **[P1] The rollback vector now fails where it claims to.** It raised from
  `_statements`, which `_migrate` calls before it has advanced the version or
  inserted the binding, so it proved only that an exception just after
  `BEGIN IMMEDIATE` changes nothing. The hook now sits on the final
  in-transaction validation and raises only once BOTH durable values are
  readable on the migration connection and the COMMIT has not run, asserting
  that it saw them; every prior assertion about version, binding, identities,
  receipts, bytes and later migratability is kept.
  Measured rather than argued: a mutant that moves the binding insert to after
  the COMMIT is killed by the strengthened case and PASSES the superseded one
  (13 cases OK). That mutant is the implementation the old vector could not
  have told apart.
- **[P2] The stale-opener case takes the byte snapshot.** The winner's
  finished database is read immediately before the loser's `_migrate` and
  compared immediately after, so the loser is proved to write nothing at all.
  The adjacent wrong-UUID open covers a store that was already current and
  never enters the stale migration path this finding is about.
- **Evidence text corrected.** "mid-migration" overstated where the old
  injection sat; the record and the manifest now say where the failure is
  raised and what has been written by then.

### Still open

Independent review.

## 2026-09-04 — baton.claude — rebase onto the integrated W85500

The 09-30-00Z proposal was signed off by `review-2026-09-04T13-34-14Z.md` and
then refused by `baton.merge` at 13:36:14Z, because all seventeen modified
targets held candidate bytes rather than base bytes. The operator did not ask
for that to be re-argued: it gated this Work behind W85500 and rerouted it here
with "rebase the approved authority-namespacing correction onto its integrated
result, produce a fresh immutable proposal, and return it for independent
review." W85500 is now closed and integrated. This is that rebase and nothing
else — no finding was reopened and no accepted behaviour was redesigned.

### What moved, and how it was merged

Base moves from `389cdd4` to `d33cdbf`. Two commits landed in between:
`0650c61`, carrying W85500's twelve source paths and several other Works'
source, and `d33cdbf`, carrying W85500's dossier. Seven of this candidate's
seventeen source paths moved underneath it; the other ten are byte-identical at
both bases and their candidate bytes applied unchanged.

Merged with `diff3` per path — mine the path at `d33cdbf`, ancestor the path at
`389cdd4`, theirs the signed-off candidate byte for byte. No mutating Git
operation was used and none was available: this deployment's hook refuses every
patch-application invocation, including the read-only check form. Six of the
seven merged with no textual conflict; `DEPLOYMENT.md` had one, where both
sides append an independent section to the same chapter.

**A clean textual merge was not a correct merge, and the suites are what said
so.** Six paths merged without a conflict and three of them were still wrong.
W85500's cases and its documented example were written when `status` took no
Authority operand, and this correction makes `--authority-uuid` required on all
three commands — so a merge that touched neither side's lines produced five
cases exiting 2 from argparse and one documented invocation this build refuses.
Nothing in the diff would have shown that.

### The delta from what was signed off, measured per path

For each of the seventeen paths I compared the added and removed lines of
`389cdd4 → signed-off candidate` with those of `d33cdbf → this candidate`.
**Fourteen are identical line for line.** The three that differ, and the one
whose lines match but are placed differently, are all additions — nothing
reviewed is missing from any of them:

- `tests/job_manager/test_tool.py`, +8 lines: the five submit/status
  invocations W85500 added carry `--authority-uuid`, two reflowed to fit. No
  assertion in those cases changed.
- `tests/tools/test_single_worker.py`, +1 line: the one real
  `status --observe` CLI run W85500 added carries `--authority-uuid`, naming
  the `AUTHORITY_UUID` this candidate already binds that case's Job store to.
- `tools/single_worker.py`, +16 lines, all comment, no statement changed.
- `DEPLOYMENT.md`, +1 line beyond the reviewed edit: `--authority-uuid` in
  W85500's `--observe` example. Both sections are present in full, W85500's
  status-freshness account first because it continues the chapter above it.

PLAN item 5 already names both test files as the scheduled authority to adjust
CLI operands in them.

### The one decision the rebase forced, and the one it refused

`tools.single_worker._Observation` did not exist when this correction was
approved. Its comment says its Authority-binding comparison stays out because
"W83781 is ordered behind this Work rather than integrated over it, so a
candidate here must not depend on it" — a sentence that is false in a tree
where this Work sits on top of W85500, and policy is explicit that two live
rules contradicting each other are worse than either alone.

So the comment now marks that sentence superseded and keeps the decision, with
a reason that is measurable rather than provisional: `JobStore.open` requires
the operand and refuses a foreign binding before any factory sees the store, so
a store's binding is already proved by the time it arrives; what
`operations_from` compares is the second question — the deployment
CONFIGURATION's Authority against the store's — and it compares it because
everything after that line writes, while this surface only reads.

**I did not add the comparison to the read-only surface.** It is a design
change, the approved boundary names `operations_from` and the store, and a
rebase is not where a new refusal gets introduced. `FINDING.md` pins that
ruling under "Rebase decisions" so it reads as a decision rather than an
omission.

### Verification, re-measured on the rebased tree

Job Manager 267 → 290, production single-worker composition 82 → 85, focused
OCI 111 → 113, and the two direct-run entry points at 42 and 22. All pass. The
before-figures are the NEW base, so they include W85500; the 269/74 recorded
for the signed-off proposal were measured on the old base and are not
comparable, though the candidate's own additions are the same in both.

Whole tree 3781 cases, 7 failures, 1 error, 14 skipped — the same pre-existing
boundary-inventory, authority-catalog, real-daemon host-state and
parallel-runner registry results the base produces without this candidate. The
arithmetic closes exactly: 3753 on the base plus 23 + 3 + 2.

**One number in the superseded manifest was wrong and is corrected rather than
carried.** Its test account said `tests/manager/test_oci.py` gained three
cases. Measured against the base module by loading both and differencing the
case ids, it gains exactly two —
`test_a_foreign_authoritys_container_is_refused_and_stays_refused` and
`test_a_namespaced_attempt_reaches_exactly_one_run` — and removes none. Both
reviews ran 113 with the candidate, which was right; only the delta was
overstated.

### For the integrator, stated early because it cost a cycle already

Producing and verifying this rebase requires the candidate bytes in the working
tree, so the seventeen source targets again hold candidate bytes rather than
base bytes. `baton.merge`'s target preflight will refuse for exactly the reason
it refused at 13:36:14Z unless `baton.ops` first restores those seventeen paths
to `d33cdbf` and removes the three planned-new dossier files. That is the
established shape of this cycle in this deployment, not a defect I introduced,
and I am naming it in the handoff so the restore is scheduled rather than
discovered.

### Still open

Independent review of the rebased digest-bound proposal.

## 2026-09-05 — baton.claude — response to review-2026-09-05T02-02-39Z

Two P2s, both in proposal metadata, both mine, both reproduced and corrected.
NO SOURCE, TEST, DOCUMENTATION, FINDING OR PLAN BYTE CHANGED: all seventeen
source paths and `FINDING.md` and `PLAN.md` carry the same digests they did in
the `01-56-00Z` proposal, and `PROGRESS.md` is the only path that moves.

### [P2] The corrected OCI account was written to a key nothing reads

The manifest carried two live summaries of the same edit. A top-level
`test_account` correctly said `tests/manager/test_oci.py` adds two cases and
removes none; `test_changes.account`, which is the section an integrator
actually audits for existing-test authority, still said three — the exact
number the same manifest's rebase narrative said had been measured wrong and
corrected rather than carried.

It is a packaging-script bug rather than a disagreement. The builder folds an
edits document into the prior manifest with two named merge handlers,
`corrections_append` and `test_account_append`, and everything else is assigned
as a top-level key. I wrote the corrected list under `test_account`, which is
neither handler, so it was assigned beside `test_changes` instead of replacing
the entry inside it — and because the new key looked right, nothing I checked
afterwards read the one that was wrong.

Corrected by folding the whole corrected list into `test_changes.account` and
DELETING the stray key, so there is exactly one account. The launched-fixture
and whole-label-negative-control descriptions the review asked to preserve are
kept verbatim.

### [P2] Thirteen paths, not fourteen; four deltas, not three

`rebase.verified_per_path` said fourteen of seventeen edit sets are identical
and "the three that differ are enumerated in rebase_deltas below", while
`rebase_deltas` lists four. The reviewer's count is the right one and my
measurement was the weaker instrument: I compared the added and removed lines
as MULTISETS, and `DEPLOYMENT.md`'s extra line —
`--authority-uuid 0123456789abcdef0123456789abcdef \` — is a line the reviewed
edit already added three times elsewhere, so a value-based comparison saw
nothing new. A sequence-aware comparison sees it, and it is the honest measure:
thirteen edit sequences are byte-for-byte equal and four paths differ.

**This also corrects the section above**, which says "Fourteen are identical
line for line". It is thirteen. The four deltas that section then lists are
right and unchanged, and so is every claim about what they contain: three
clean-merge semantic additions plus the resolved deployment conflict, all
additions, nothing reviewed absent. Corrected here rather than by rewriting
that paragraph, because it is the account of what the previous turn actually
measured.

`rebase.verified_per_path`, `carried_forward.note` and the rebase entry in
`corrections` now all say thirteen and four, and distinguish the three
clean-merge adjustments from the one conflict resolution whose extra line
repeats existing content at a new location.

### Verification

Nothing executable changed, so nothing was re-run and this section does not
restate counts as though it had been. The bytes were re-verified instead: `HEAD`
is still `d33cdbf`, all seventeen source paths plus `FINDING.md` and `PLAN.md`
still match the `01-56-00Z` candidate digests exactly, and `PROGRESS.md` is the
only record path that moves.

The reverse-apply check is still not runnable here; the previous review ran it
independently against the `01-56-00Z` patch with
`--whitespace=error-all` and reported it passing.

### Still open

Independent review of the regenerated proposal, and then the already-disclosed
operator restore of the seventeen targets to `d33cdbf` bytes and the three
dossier files to planned absence before `baton.merge` may import.

## 2026-09-05 — baton.claude — response to review-2026-09-05T02-09-02Z

One P2, mine, in proposal metadata, reproduced and corrected. NO SOURCE, TEST,
DOCUMENTATION, FINDING OR PLAN BYTE CHANGED, again: `PROGRESS.md` is the only
path that moves.

### [P2] A field that names the signed-off candidate stopped reading it

`unchanged_from_signed_off_candidate` was `false` on the seven rebased paths in
the `01-56-00Z` package and `true` on all seventeen in `02-06-00Z`, though no
candidate byte changed between them. Measured against the `09-30-00Z`
signed-off candidate it is ten true and seven false, exactly as the first
rebased package said and exactly what `rebase.moved_paths` names.

The cause is the previous correction's own shape. The packaging builder folds
its edits into a TEMPLATE manifest, and it also derived this flag from that
template. For the rebase that was harmless, because the template was the
signed-off package. For a metadata-only regeneration the template is the
immediate predecessor — so repointing it to `01-56-00Z` silently changed what
the flag compared against, and every path came back identical because every
path IS identical to the package one round earlier. The field kept its name and
lost its referent.

Two P2s in a row now have the same shape: a packaging change that was right in
itself, quietly altering a value nothing re-derived. So the fix is not just the
flag. The builder now holds the signed-off locator in its own constant, reads
the flag's reference from there, and never follows the template; the reason is
written at the site. `recomputation` states which locator the field compares
against, so the manifest says what the flag means rather than leaving a reader
to infer it from a name.

The distinction the review draws is the one that matters and is why the wrong
answer was plausible: those seven paths combine W85500 with W83781, which is
precisely why they were re-reviewed rather than carried, and a flag calling
them unchanged would tell an integrator the opposite of the thing the rebase
narrative spends four entries explaining.

### Verification

Nothing executable changed, so nothing was re-run. The bytes were re-verified:
`HEAD` is still `d33cdbf`, all seventeen source paths plus `FINDING.md` and
`PLAN.md` still carry the `02-06-00Z` candidate digests, and the seven flags are
now recomputed directly against the archived `09-30-00Z` candidate bytes rather
than against any template.

### Still open

Independent review of the corrected proposal, then the operator restore of the
seventeen targets to `d33cdbf` bytes and the three dossier files to planned
absence before `baton.merge` may import.

## 2026-09-05 — baton.claude — response to review-2026-09-05T02-14-05Z

One P2, one sentence, mine. NO SOURCE, TEST, DOCUMENTATION, FINDING OR PLAN
BYTE CHANGED; `PROGRESS.md` is again the only path that moves.

### [P2] The recomputation account described the defect backwards

The sentence I added to `manifest.json.recomputation` said review
`02-09-02Z` "returned it as false on all seventeen paths". It returned the
opposite: the `02-06-00Z` proposal had `unchanged_from_signed_off_candidate`
**true** on all seventeen, and the review returned it because the seven rebased
paths must be **false**. The clause also contradicted the correct ten-true /
seven-false split in its own next line, and both `PROGRESS.md` and the
manifest's own `corrections` entry state the real history.

Corrected to say what happened: the `02-06-00Z` package carried all seventeen
flags true, and review `02-09-02Z` returned the seven rebased paths for
correction to false. Nothing else in `recomputation` changed — the fixed
signed-off locator, the "not the immediate predecessor" sentence and the
ten/seven values are preserved as reviewed.

It is worth naming what this was, since it is the third metadata round: not a
measurement error but a sentence written from memory while the correction it
described was already in hand. The flags and the builder fix were right; the
prose about them was not, and prose in a manifest is what an integrator reads.

### Verification

Nothing executable changed, so nothing was re-run. `HEAD` is still `d33cdbf`,
all seventeen source paths plus `FINDING.md` and `PLAN.md` still carry the
`02-11-00Z` candidate digests, and the ten-true / seven-false flags are
recomputed against the archived `09-30-00Z` candidate bytes and still match
`rebase.moved_paths` exactly.

### Still open

Independent review of the corrected proposal, then the operator restore of the
seventeen targets to `d33cdbf` bytes and the three dossier files to planned
absence before `baton.merge` may import.
