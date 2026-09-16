# Progress — baton.tuner, claim178579

2026-09-15: owner178575 bounded dossier fixture preparation completed. Revalidated
all nineteen prior inputs in BASELINE-178579.json, preserved the original packet
and handoff, and pinned the explicit supersessions in FINDING before fixture work.
Created only dossier runtime helpers, focused offline tests, manifest, supervisor,
operator recipe and retained evidence/candidate copies. No product path changed.

The final candidate manifest is `26a0f74254f88d49e02420c05b242c3349dc6b30b567666928be7290019ded2f`. All 22 focused tests pass;
`offline-178579-candidate.json` records 0.263774633s,
exit0, no timeout and positive owned-process-group absence. Four preparation
iterations total 1.054891332s measured supervisor time. Earlier logs remain
history; only the candidate receipt binds final bytes. Audit passes. Tests use
synthetic engine/provider state and bounded local Python processes only; no live
engine, model, credential, image build/pull or production enablement occurred.

Current state: awaiting independent fixture review at baton.feat, then baton.ops
for concrete live-run selection. HANDOFF-178579.md and OPERATOR-178579.md carry the
exact remaining scope. G1–G6 are still live qualification gaps. Ordinary focused
verification has standing authority; no cumulative stopwatch gate is claimed.

## Claim 178875 — the bounded R1/R2 correction

Owner reroute 178872 assigns the two findings of `review-2026-09-15T14-36-52Z.md`
to baton.claude while the tuner continues W161234 B. Corrected the dossier
fixture, its contract tests and the operator packet only; **the submitted
candidate bytes were revalidated against the review's four inventoried hashes
before any edit**, and `candidate-178875/` retains the corrected set.

**R1 — the restored working copy is writable by the runtime it is for.**
`private_file` gained an explicit `writable` operand. The reconstructed per-use
session state is created `0660` in the workspace group; **every other object is
untouched** — the credential slot copy and the request document are the
container's read-only inputs and stay `0640`, manager-private files stay `0600`,
and the immutable source generation is not modified. Setgid on the parent
supplies group identity, not file write permission, and that is the distinction
the earlier `0640` lost: the experiment would have qualified a read-only input
under the name of a writable working copy, so a negative result would not have
meant what the packet says it means. This is **not** a claim the CLI would
certainly have failed — a group-writable parent may permit unlink-and-replace,
and the provider's write strategy stays unobserved.

**R2 — the whole run identity is reserved before anything is admitted.** Run,
volatile and export are now taken exclusively before the controller starts, so
an existing export root refuses before any credential or engine use rather than
after both live turns had been paid for. A foreign path at any of the three
stops the run and is never repaired; a partial reservation unwinds. The
operator packet's claim that all three refuse before engine or credential use
was false when written and is now true, and its pinned manifest digest moved
with the bytes.

**Verification: 29 tests (22 before, 7 added), OK, 0.2638512429839466 s**, exit
0, no timeout, owned process group positively absent — receipt at
`evidence/corrected-178875.json`.

**Four reversal probes, each reverting one guard, each failing exactly where it
should.** A first batch run mis-attributed one probe's failures, and the cause
was found rather than worked around: the two patched variants are byte-identical
in **length** and landed in the same mtime second, so Python's source cache —
which validates on mtime and size — served the previous probe's bytecode. Every
probe was re-run with `__pycache__` removed and `-B`. That artifact is recorded
in `EVIDENCE-178875.json` rather than tidied away, because a probe whose result
comes from stale bytecode is not evidence.

No live execution, engine, model, credential use, image build or pull, product
edit, broad suite, baseline repair or version-control operation. **G1–G6 remain
unqualified**; G7 stays the qualification-only image selection; G8 is not
composed. No gate or interruption to W161234 B.

Evidence: `EVIDENCE-178875.json`
`sha256:b2962d220f7c8eb166b8fe9aab2db7f9884fa144c8cb10453fd6d56e90e6e986`.

## Claim 179146 — the selected artifact/model correction

Owner reroute 179142 selects the correction proposed by
`review-2026-09-15T15-16-11Z.md` after the operator's failed live run. The
acceptance supersession was pinned in FINDING and PLAN **before any source
edit**, and the accepted 178875 bytes were revalidated first: the four fixture
files matched manifest `73fe32b9…` and OPERATOR-178579.md matched `e504579f…`.
Five files changed, all inside this dossier; `candidate-179146/` retains the set
and the two earlier candidates are intact as history.

**A — `solution.py` is accepted with or without its one final LF.** Run179075
wrote the expected 38 bytes with the final newline absent. The exact-byte guard
enforced the contract that was selected and refused correctly; requiring that
newline was never part of the multiply-by-two/three and continuity question. So
this is a bounded acceptance decision, not a bug fix, and it does not turn the
failed run into a pass. The relaxation is exactly one newline wide — an extra
final LF, leading whitespace, horizontal trailing whitespace, altered
indentation, an altered multiplier, an added comment, CRLF endings and any extra
or missing workspace entry all still refuse, and a source-level test asserts that
no `strip()`, normalization or `replace()` was introduced into the check.
**`continuity.txt` did not move**: token plus one newline, exactly.

**A constant is not an observation.** The old export named `sha(INITIAL)` as
`initial_artifact_sha256`, which was harmless only while equality was exact.
Expected and observed are now separately named, and the observed digest, byte
length and form are recorded **before** the refusal — run179075 exported a bare
failure code, and learning what the provider had actually written took a separate
operator diagnostic afterwards. The controller still never writes to the
workspace: refused bytes are left exactly as the provider wrote them.

**B — the export records why a model did not qualify, never which one.**
`modelUsage` was present and failed its singleton-key predicate while `model` was
absent, and the projection could not tell a non-object, an empty object, one
other key and several apart. The raw provider document is read from an anonymous
bounded pipe and never retained, so no later inspection recovers that — only the
next run can. Closed type/cardinality/expected-key diagnostics with a key count
bounded at 8 and an explicit overflow flag now carry it, and `consistent()`
refuses at the arm any record whose diagnostics contradict its own verdict. **The
acceptance predicate is unchanged in every case**, and no model name, value,
usage payload or prose is exported. The worker is untouched — it forwards the
closed projection whole, and its manifest digest is the one accepted at 178875.

**Verification: 51 tests (29 before, 22 added), OK, 0.2638050550012849 s**,
exit0, no timeout, owned process group positively absent — receipt
`evidence/corrected-179146.json`, produced by this dossier's own
`verify-offline.py`. Seven reversal probes in `evidence/probes-179146.json`, each
reverting one guard in an isolated copy with its manifest recomputed,
`__pycache__` removed and `-B`, each failing exactly where it should.

**ONE PROBE PASSED ON THE FIRST BATCH, AND THAT WAS A REAL GAP RATHER THAN A
HARNESS ARTIFACT.** Reordering the first-turn record to sit after its refusal
broke nothing, because no test drove a first-turn artifact mismatch at all — the
observed-before-refused requirement was only covered at the second turn, which is
not where run179075 failed. `test_a_refused_first_turn_artifact_is_recorded_before_it_is_refused`
and a matching second-turn ordering probe were added; all seven then failed.

The approved manifest moved to
`9a1ddd250da674e956c707f043830863d74db9074814b5050dff5d5c6c5b78ff`; `73fe32b9…`
and `26a0f742…` are both refused by `--approved-manifest`. Not done and not
claimed: no live execution, engine, model, credential use, image work, product or
consumer edit, broad suite, baseline repair, marker reset, new run identity or
version-control operation. **The consumed fixed identity is not reused** and the
markers from run179075 are left as they are. G1 stays partial with no accepted
actual model, G4/G6 first-use only, G2/G3/G5 unobserved, G7 qualification-only,
G8 not composed. Production qualification remains incomplete; no gate or
interruption to W161234 B.

## Claim 179295 — R1, the diagnostic relationships

Owner reroute 179288 selects R1 from `review-2026-09-15T15-39-27Z.md`, inside the
owner179142 scope. All nine reviewed inputs were revalidated at their recorded
hashes before any edit, and the current action was pinned in FINDING and PLAN
first. **Two files changed** — `evidence/qualification_contract.py` and
`evidence/test_qualification.py` — plus the manifest, operator packet, candidate
and evidence. The controller, the worker, the offline supervisor and the whole
artifact half are byte-identical to the accepted 179146 correction.

**THE DEFECT WAS MINE AND IT WAS REAL.** `consistent()` validated the diagnostic
members' types, ranges and boolean identity, and their agreement with the
verdict — and then never checked that they agree with **each other**. I
reproduced all four reviewed records through the real arm before touching
anything, and four more that follow from the same gap: `expected-only` reporting
two keys, `expected-only` reporting eight with overflow, overflow at one key,
`modelUsage` credited with supplying the model while absent from the closed
`members` list, `empty-object` with overflow, `expected-plus-other` with one key,
`other-only` with one key and overflow, and a `model` diagnostic of `expected`
for a field `members` says was absent. A guard that type-checks a vocabulary
without relating its terms is not a guard.

The finite relationships are now a table: `missing` means the known member is
absent and every other diagnostic means it is present, for both fields;
`empty-object` is count0 uncapped; `expected-only` is count1 uncapped;
`other-only` has a positive count; `expected-plus-other` has at least two; and
overflow requires exactly the cap on a shape that can hold more keys than that.
`MODEL_KEY_CAP` stays 8, the strict int/bool identity checks stay, and **the
actual-model predicate is untouched** — this qualifies no model that was not
already qualified and refuses none that was. Boundary positives at 0/1/2/8/9 keys
with and without the expected key, plus absent and wrong-type, all hold.

**Scope.** A malformed-record admission gap, not a claim that the pinned provider
emitted these contradictions — the review's own 80-vector matrix found the
unchanged worker projection coherent throughout. It matters because a strict
closed boundary that admits self-contradictory evidence is not strict.

**Verification: 60 tests (51 before, 9 added), OK, 0.2636633020010777 s**, exit0,
no timeout, owned process group positively absent — receipt
`evidence/corrected-179295.json`. Twelve reversal probes in
`evidence/probes-179146.json`, each in an isolated copy with its manifest
recomputed, `__pycache__` removed and `-B`.

**TWO PROBES PASSED ON THE FIRST BATCH, AND THEY MEANT DIFFERENT THINGS.** The
first was a genuine gap: nothing flipped `model_usage_expected_key` to a
valid-but-wrong boolean, so only the identity check — which catches `1`, not
`False` — covered that rule; a contract test and an arm-level case were added and
it then failed. The second was not a gap at all: substituting
`shape["high"] == MODEL_KEY_CAP` for the named `OVERFLOW_SHAPES` membership is
exactly equivalent at cap 8, so the probe reverted nothing. **I removed it rather
than counting it, and corrected the source comment that had claimed the naming
guarded against a reachable fault** — it is a readability choice, and saying
otherwise in a comment would have been a small false claim left in the tree.

The approved manifest moved to
`3d5684edae17c296827db26c2a1dcffbf5173d719ddb80fe8e5f1e25f6f98741`; `9a1ddd25…`,
`73fe32b9…` and `26a0f742…` are all refused. Not done and not claimed: no live
execution, engine, model, credential use, image work, product or consumer edit,
broad suite, baseline repair, marker reset, new run identity, model acceptance
relaxation, validation redesign or version-control operation. The consumed fixed
identity is not reused and run179075's markers are untouched. G1 stays partial
with no accepted actual model, G4/G6 first-use only, G2/G3/G5 unobserved, G7
qualification-only, G8 not composed. Production qualification remains incomplete;
no gate or interruption to W161234 B.

## Claim 180078 — the fresh run identity

Owner reroute180071 selects the bounded fresh-identity preparation; the current
action was already pinned in FINDING and PLAN by the owner. All nine accepted
inputs were revalidated at their recorded hashes before any edit.

**The consumed identity is retired, not reset.** Run179075 took all three fixed
roots of 178579, and the fixture refuses a taken root rather than repairing it —
accepted behaviour, and the whole reason a rerun needs a new name. Those roots
keep their original 09:02 timestamps and their evidence. A new test asserts that
nothing executable in the fixture or the contract can name them; it is asserted
over **comment-stripped** source, because the first version of it failed on my
own explanatory comment and banning the history from being explained would have
been the wrong fix. The fresh identity is `180078`, its three roots were
confirmed free, and **none was created** — this preparation reserves nothing.

**The manifest now binds the identity, not just the bytes.** `audit` requires
`run_identity`, `private_root`, `credential_copy_root` and the new `export_root`
to equal the roots this fixture would actually reserve. Those fields were
decorative before: an approved manifest could have named one identity while the
code took another and the digest would still have verified. Changing any one of
the four alone now refuses with `manifest-constants`. The export root is derived
from the run root in one place, used by both `audit` and `run` — a second copy of
that derivation is exactly how a declared and a reserved name drift apart. That
single-source change also kept the R2 tests honest: they patch `ROOT` to a
temporary directory, and a module-level constant would have stopped following it.

Delta: fixture, tests, manifest, operator packet. `qualification_contract.py`,
`qualification_worker.py` and `verify-offline.py` are byte-identical to accepted
correction179295, so the image, two turns, 180s per invocation, 600s envelope and
all artifact/continuity/custody/shutdown/model behaviour reuse that acceptance.

**Verification: 67 tests (60 before, 7 added), OK, 0.26378964600735344 s**, exit0,
no timeout, owned process group positively absent — receipt
`evidence/identity-180078.json`. Fifteen reversal probes in
`evidence/probes-179146.json`, each in an isolated copy with its manifest
recomputed, `__pycache__` removed and `-B`; the three new ones put the consumed
identity back, drop the declared-root check and pin the export root separately.

The approved manifest moved to
`5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f`; the four
earlier digests are all refused. The operator packet keeps its `178579` filename
on purpose — each review pinned it by hash — with a note that the filename
records the packet's origin, not the run identity, since the last reviewer hit
exactly that confusion.

**This prepares an identity; it does not authorize a run.** No live model, engine,
credential, network or image operation, no root reserved, the fixture never
launched, no marker reset, no product or consumer edit, no version-control
operation. Selecting the run, its executor and the moment is a separate
baton.ops decision. G1 partial without an accepted actual model, G4/G6 first-use
only, G2/G3/G5 unobserved, G7 qualification-only, G8 not composed. Production
qualification remains incomplete; no gate or interruption to W161234.

**One more thing, found by a check rather than a test.** The first version of the
`export-root-pinned-not-derived` probe returned a hard-coded
`/tmp/baton-w177936-qualification-180078-export` literal, so when the patched
tests called `run()` the reservation loop created the **real** directory. A probe
reached outside its sandbox and quietly consumed the very identity this turn
prepares — the post-verification check that all three fresh roots were still
unreserved is what caught it, not any test. The empty `0700` directory was mine
and minutes old; I removed it, changed the probe to derive from `VOLATILE` so it
stays inside the temporary tree, and re-ran. All fifteen probes still fail as
required and all three fresh roots are confirmed unreserved.

## Claim 180339 — the fixed-path metadata diagnostic

Owner180325 selected the **first proposal only** of
`review-2026-09-15T18-36-00Z.md`. The selection was pinned in FINDING and PLAN
before anything was written. Three new files, all in this dossier:
`diagnostic-180078.py`, `diagnostic-180078-selftest.py` and
`OPERATOR-DIAGNOSTIC-180339.md`, with `EVIDENCE-180339.json` binding them.
**No accepted fixture file was touched** — the manifest is still `5e789f4e…`.

**The private tree was not inspected from here, and that is the point.** The
review is explicit that a managed sandbox's mount and PID view is not the
operator's. This context is uid1000 with groups {1000, 65534} — a different
identity from the one that ran collection — so reading the tree from here would
have answered the wrong question while looking like an answer. The script is
written for the host, verified against a synthetic tree, and handed over.

**Closed by construction, not by intention.** Never opens a regular file, lists
or traverses a directory, calls `readlink`, writes, chmods, chowns, or resolves a
user or group **name** — account names are arbitrary strings, so identity is
numbers only. Every operand label is a source constant, so nothing the tree
contains can become a label. It takes no arguments and refuses any with exit 2:
a path operand would turn a fixed-path diagnostic into a general private-tree
reader.

**No component is followed, not just the last one.** Plain `lstat` protects only
the final component: if `use-1/home` were a symlink, an `lstat` of
`use-1/home/.claude` would silently describe a different location and read as a
clean answer. Each operand is walked component by component through
`O_PATH|O_NOFOLLOW|O_DIRECTORY` descriptors instead.

**Verification: 14 self-tests, OK**, against synthetic temporary trees only —
present/absent rows and the closed field set; a symlinked intermediate refused
rather than resolved; an unsearchable directory reporting EACCES; a
non-directory component reporting ENOTDIR; canaries planted as a project name, a
session filename, file content and a link target, none reaching the export; and
a before/after walk proving that looking at the tree does not modify it. A
static check over comment-stripped source confirms the forbidden calls are
absent from executable text and that both `os.open` calls carry the no-follow
directory flags.

**A correction I made to my own draft.** The docstring, FINDING and PLAN first
said a symlinked intermediate "surfaces as ELOOP". The self-test failed on that
assertion: Linux returns **ENOTDIR**, because `O_DIRECTORY` is consulted before
`O_NOFOLLOW`. The guard worked and my wording named the wrong code. Both codes
are inside the review's closed enum, so the operator sees a refusal either way —
I corrected all three places because the claim would have read as a defect
against real output, and a test that only confirms what I already believe is not
worth running.

**Identity180078 stays consumed.** Metadata inspection cannot convert its result
into success, and the packet says so: no chmod, chown, repair, marker reset,
identity switch, fixture rerun or new identity on the strength of this output — a
permission or copying change needs its own bounded rationale and must not be
bundled with a guess. All six consumed roots across both identities keep their
original timestamps. Model acceptance is unchanged and G1 stays unqualified.

Not selected and not prepared: the conditional bounded no-content walk of the two
homes, and the closed collection step/category/errno fixture correction. Either
may follow from reading this output. New measured verification: the 14-test
self-test only; no live provider, engine, credential, image or private-tree
access, no product or consumer edit, no Git operation.

## Claim 180413 — the bounded metadata-only home walk

Owner180411 selected the review's **second, conditional** proposal after the
operator's fixed-path result. Pinned in FINDING and PLAN before implementation.
Four new files, all in this dossier: `walk-180078.py`,
`walk-180078-selftest.py`, `probes-180413.py` and `OPERATOR-WALK-180413.md`,
bound by `EVIDENCE-180413.json`. **No accepted fixture file was touched** — the
manifest is still `5e789f4e…`.

**The fixed-path result aimed this.** `private-layout.json`, its tmp sibling and
every `use-2` operand are absent, so the run stopped before the layout save —
inside first inventory or subset selection. `inventory` reads and hashes every
admitted regular file, and the fixed paths could only show the five top
directories are mode-permitted. `use-1/home/.claude/projects` is uid65532 gid1001
mode `0o2755`, which is where the runtime's own files begin, and a nested file
the collector could not open is the hypothesis still standing.

**Bounds as selected**: 1024 entries per home, depth 8, 20 s wall. Reaching one
is reported, never absorbed — a truncated walk that looked complete would be
worse than no walk. Aggregates only, grouped by type/uid/gid/mode/readable/
searchable; links counted and never resolved; credential-shaped entries skipped
using **the fixture's own regex**, so the walk stops exactly where the collector
stops instead of inventing a second rule. `use-2/home` is absent and reported
absent, not as an error.

**Verification: 21 self-tests, OK**, synthetic trees only, plus **ten reversal
probes each failing where it should**, in isolated copies with `__pycache__`
removed and `-B`.

**Three things the probes taught me, two of which were my own mistakes.**

The `O_NOFOLLOW` probe **passed** at first: only the static source check noticed
it, so nothing *proved* it mattered. The gap was real — the home's own path is
where a following open would walk a decoy and report it as the home — and
`test_a_symlinked_home_component_is_refused_not_walked` now covers it.

The error-handler probe **passed**, and taught me I had mislabelled my own test.
Mode `0600` on a directory is *readable*, so it opens and scandirs fine and the
failure lands on the **stat** handler, not `opendir`. My test was passing for a
different reason than its name claimed. Renamed, and
`test_an_unopenable_directory_reports_an_opendir_error` added for mode `0000`.

A `wider-export-names` probe was tried and **removed rather than counted**:
widening the export name list reverts nothing, because `zip` truncates against
the six-element key, so a name can only leak if the key is widened too — which
another probe covers. Two independent changes are needed for a leak. That is a
property of the code, not a gap in the tests, and counting it would have inflated
the probe total with a probe that proves nothing.

**The private tree was not walked from here**, and beyond the instruction there
is a substantive reason: the read/search classification is relative to the
identity running the script, so an answer computed under this context's identity
would be confidently wrong rather than merely useless.

**What it still cannot do**, stated in the packet rather than left to be
discovered: POSIX bits ignore ACLs and namespaces, so permitted is not proof of
readability and denied is not proof of the failure; and the original exception
was never retained, so no metadata inspection recovers it — that needs the
separate closed-diagnostics fixture correction, which stays unselected.

Identity180078 stays consumed; all six roots across both identities keep their
timestamps; model acceptance unchanged and G1 unqualified. No live provider,
engine, credential or image operation, no product or consumer edit, no Git
operation.

## Claim 180537 — the bounded collection/custody correction proposal

Owner180530 asked for the smallest collection/custody correction as a **concrete
proposal**, not an implementation. Delivered as
`CORRECTION-PROPOSAL-180537.md` with `EVIDENCE-180537.json`. Pinned in FINDING
and PLAN first. **Nothing was implemented and no fixture file was touched** — the
accepted manifest is still `5e789f4e…`.

**The inference the whole fix turns on, checked before proposing rather than
after.** The obvious smallest fix is a container umask: one line. It cannot work.
The runtime created *both* permissive objects (`0o2755` directories, a `0o644`
file) and restrictive ones (`0o700` directory, `0o600` files), and one umask
cannot produce both, because umask only ever removes bits. The `0o700` directory
clinches it: gid1001 with **no setgid bit**, which a child of a setgid parent
inherits automatically — so something chmodded it after creation. The restrictive
modes are explicit, and umask never adds bits back.

**What the evidence means.** Setgid gave group *ownership* and never group
*permission bits* — the same distinction accepted R1 turned on at 178875,
arriving from the opposite direction. There the manager had to make a file the
runtime could write; here the runtime makes files the manager cannot read.

**The proposal:** the worker — the identity that owns the files — relaxes exactly
two objects it created, the one observed project directory and its expected
session JSONL, refusing on any other shape; `inventory` records an unreadable
*non-selected* entry closed instead of dying, while an unreadable *selected* file
still refuses with a specific code; and the review's closed collection
step/category/errno diagnostics come along, because they are what would make the
next failure attributable instead of `unclassified`.

**Written to be correct whichever way the unknowns fall.** The aggregate cannot
say which directory produced the EACCES, whether it holds the selected session,
or which operation failed, and the original exception is lost. I said so in the
proposal rather than picking the reading that flatters the fix.

**The larger alternative is deferred, not dismissed.** Collecting as uid65532 —
the runtime publishing rather than the manager scraping — is a coherent design.
Evidence of the symptom is not evidence that it is the smallest cure, and it
deserves a deliberate selection rather than being arrived at by accident. A
manager-side chmod is rejected outright: that is the host granting itself access
to another identity's files.

No implementation, further private-tree exploration, consumed-tree repair, chmod
or chown of either consumed tree, live rerun, fresh identity or model-acceptance
change. Both consumed root sets keep their timestamps; G1 stays unqualified;
W161234, C1 and C2 independent. New measured verification 0 s.

## Claim 180580 — proposal revision 2

Owner180577 returned revision 1 with two defects. **Both were real and both were
mine**, and revision 2 describes them in §2 rather than quietly repairing them.
Still a proposal; the accepted fixture is untouched at manifest `5e789f4e…`.

**D1 — I would have made three absence claims vacuous.** I wrote that an
unreadable entry should be "recorded closed instead of raising" without asking
what the fixture asserts from directory listings. It asserts three *negatives* —
`unexpected-credential-entry` home-wide, `project-key-ambiguous`,
`foreign-session-state` — and an unenterable directory hides exactly the names
they are about. My tolerance would have reported those checks as passed without
looking. That is the vacuous-assertion failure this campaign has caught twice
before; this time I introduced it.

The fix came from asking what each claim actually reads. All three are
**name-based**, and a name is visible in the parent's listing. So an unreadable
**file** is safe to record closed — only its digest is lost — and an unenterable
**directory** must refuse. The tolerance is now exactly as wide as the evidence
stays sound and no wider.

**D2 — I did not separate the two turns, and aimed at the accepted R1 object.**
Turn 2's home is *manager*-reconstructed and its restored session file is
`0o660` owned by uid1000 — the writable working copy R1 established at 178875.
My turn-agnostic wording pointed a chmod at it. It would have failed EPERM rather
than corrupting anything, since uid65532 cannot chmod a uid1000 file, so the
damage was bounded — but the intent was wrong. P1a is now turn-1 only and
runtime-owned only, with type, uid and gid verified through the **same no-follow
descriptor that is then `fchmod`ed**, so there is no check-to-change window.

**And one thing revision 1 should have said.** If the blocking `0o700` directory
is not the project directory, the correction does **not** make the run pass: P1a
relaxes two named objects and P1b then refuses at `state-coverage-incomplete`.
That is still better than today — the export names the step and errno instead of
`unclassified` — but it is a refusal, and implying a pass would have been selling
a guess. Widening P1a to relax every runtime-owned directory would make the run
pass and qualify nothing, so it stays rejected; collecting as uid65532 stays the
deferred larger candidate, and these diagnostics are what would justify it.

Two regression tests now carry the defects directly: turn 2 must leave a
manager-owned `0o660` restored file at `0o660`, and an unenterable directory
*containing* a foreign `.jsonl` and a credential-shaped entry must refuse rather
than report those absence checks as passed.

No implementation, private-tree inspection, consumed-tree repair, chmod or chown
of either consumed tree, live rerun, fresh identity or model-acceptance change.
Both consumed root sets keep their timestamps; G1 stays unqualified;
W161234/C1/C2 independent. New measured verification 0 s.

## Claim 182264 — the collection/custody correction implemented

Owner182261 selected `CORRECTION-PROPOSAL-180537.md` revision 2 for bounded
implementation. All seven accepted inputs revalidated and the selection pinned in
FINDING/PLAN before any edit. Six named paths changed and no others;
`verify-offline.py` is byte-identical.

**P1a** — turn-1-only, runtime-owned-only relaxation of exactly the observed
project directory (`0o2750`, setgid kept) and its expected session file
(`0o640`), with type, owner and group verified through **the same `O_NOFOLLOW`
descriptor that is then `fchmod`ed**. One design change I made while writing it:
ownership is checked against `os.geteuid()` rather than a hard-coded `65532`.
"Runtime-owned" means *owned by me*, and a constant can drift; `main`'s existing
`worker-identity` check still pins that the worker is 65532, so the two together
say exactly what is meant. Turn 2 relaxes nothing, so the manager-owned `0o660`
restored working copy accepted at R1 stands.

**P1b** — unreadable **content** is tolerated, unreadable **structure** never is.
A failed `scandir` *or* a failed per-entry `stat` refuses
`state-coverage-incomplete`, because all three absence claims are name-based.
The stat case is not hypothetical: a `0o600` directory is readable, so `scandir`
succeeds and each child's `stat` is what fails — the exact shape the operator
walk observed. An unreadable selected session refuses at `subset` rather than
surfacing later as a digest mismatch.

**P1c** — a closed step, failure category and errno category on every failure,
refused at the projection boundary if malformed or if a refusal claims an errno.

**Verification: 85 tests (67 before, 18 added), OK, 0.3138183479895815 s**,
exit 0, no timeout, owned process group positively absent — receipt
`evidence/corrected-182264.json`. **Twenty-two reversal probes**, seven of them
new, each failing exactly where it should.

The two returned defects have direct regression tests:
`test_turn_two_publishes_nothing_and_the_restored_copy_stands` holds a
manager-owned `0o660` file at `0o660`, and
`test_an_unenterable_directory_refuses_rather_than_reporting_absence` hides a
foreign `.jsonl` *and* a credential-shaped entry inside the blocked directory, so
tolerating it would report those absence checks as passed.

**Two things worth stating plainly.** The synthetic trees use mode `0o000` rather
than `0o700`/`0o600`, because this process owns its fixtures and only a zeroed
owner triad denies it — the FakeEngine still creates state at `0o700`/`0o600` and
applies P1a, so the controller path exercises the real sequence. And the
correction does **not** promise a passing run: if the blocking directory is not
the project directory it refuses at `state-coverage-incomplete` with a named step
and errno, which `test_a_blocked_directory_names_its_step_and_errno` asserts.

No live execution, engine, model, credential use, image or network operation,
product or consumer edit, consumed-tree repair, marker reset, new run identity or
model-acceptance change. Both consumed root sets keep their timestamps; G1 stays
unqualified; W161234/C1/C2 independent.

## Claim 182771 — R1–R3 corrected

Review182326 withheld acceptance on three defects. **All three were real and all
three were mine**, and each was the same kind of error: the boundary the code
enforced was narrower than the boundary I claimed for it.

**R1 — my no-follow bound one component, not the path.** I wrote that "nothing
can be swapped between check and change". True of each individual descriptor,
and not true of the *path* — which is what an attacker or a race actually moves.
The reviewer demonstrated three consequences: a symlinked `.claude/projects`
published an object **outside HOME**, a rename-and-replace between the directory
check and the session's pathname reopen landed the chmod on a decoy, and a
hardlinked session was changed through its alias, which the manager's later
hardlink refusal cannot undo. Traversal is now anchored at the verified home,
every component opens relative to its verified parent, `O_NONBLOCK` stops a
special-file substitution blocking before `fstat`, and a multi-link selected file
refuses before any mode change.

**R2 — I changed forbidden layouts before refusing them.** The proposal's own
§3a says a foreign session, a nested session and a credential-shaped entry must
"refuse and relax nothing"; my `publish` checked one directory and a filename, so
each of them still published. The complete survey now finishes and the
descriptors are acquired **before the first `fchmod`**.

**R3 — my coverage refusal discarded the errno it existed to report, and my test
asserted the loss.** `test_a_blocked_directory_names_its_step_and_errno` expected
`errno: none` while its name promised the opposite. A test that asserts the bug
is worse than no test. A closed `cause` now carries the wrapped errno, with both
relationships stated at the projection boundary.

**Also delivered, because the review was right that they were missing:** the
eight-step × four-kind fault matrix injected at the **real** collection
operations — selected by argument predicate, not call-occurrence, since `save`
and `inventory` are each used at several steps and an index would drift silently
— a wrong-UID guard distinct from the GID one, and the FakeEngine now calling the
**real** `worker.publish` instead of simulating it, which is why two existing
tests changed behaviour: a credential-shaped entry now refuses in the worker
before publication rather than in the manager after it.

**Three evidence attributions corrected, history kept.** The observed operator
result is `opendir:EACCES` on a runtime-owned `0o700` directory — the `0o600`
stat seam is a useful additional regression that I had presented as the observed
shape. The collection failure is identity **180078**; 179075 was the earlier
initial-artifact failure. And mixed modes do not by themselves prove a `chmod`:
different creation modes share one umask. What survives is the part that carries
the conclusion — an explicitly requested `0o600` cannot be made group-readable by
loosening umask — so "a umask change cannot fix this" stands while "something
chmodded it" was more than the metadata supports.

**Verification: 95 tests, OK, 0.3638601779821329 s**, exit 0, no timeout, owned
process group positively absent. **Twenty-eight reversal probes**, each failing
where it should. One probe was **removed and recorded** rather than counted:
`publish-follows-symlinks` reverted a line R1 deleted, so
`publish-follows-ancestors` replaces it; and `publish-without-ownership` was
**split** into uid and gid probes, since ownership is two conditions.

Preserved: turn-2 no-op and the restored `0o660` contract, complete-structure
refusal, the strict model/artifact/continuity contracts, the image, run identity
and limits. No private-tree inspection, consumed-root repair, live execution,
fresh identity, product expansion or model-policy change.

## Claim 182906 — completing R1 and R2

Review182843 verified R3 and found R1 and R2 still incomplete. **Both findings
were right, and both were the same mistake**: I fixed the case the previous
review demonstrated instead of the class it belonged to.

**R1 — I retained nothing.** I made the survey walk descriptors and then, at the
end, **reopened the targets by path**. The swap simply moved later: a regular
decoy put in the project's place *after* the survey redirects the chmod onto an
unsurveyed file while the original keeps its mode. Verifying a descriptor is
worthless if it is not the one you then change. The targets are now the
descriptors the walk itself opened, held through selection and mutation; and a
survey that cannot complete — an entry that vanishes or refuses mid-walk —
refuses with a registered code instead of letting a raw `OSError` decide.

**R2 — my "home-wide" survey was not home-wide.** It descended only `.claude` and
the projects chain, so a credential-shaped entry under `HOME/cache` or
`HOME/.claude/cache` was invisible, and unselected invalid types elsewhere were
ignored — each publishing before the manager's inventory could refuse. The
preflight now descends the whole home under the existing entry and depth bounds
and applies the manager's own admitted-type rule, still never opening credential
or configuration contents.

**Verification: 98 tests, OK, 0.3138288449845277 s**, exit 0, no timeout, owned
process group positively absent. **Thirty reversal probes**, each failing where it
should.

**Two probes taught me something about my own probes.**
`publish-follows-ancestors` **passed**: `lstat` screens symlinks before the open
is reached, so nothing proved `O_NOFOLLOW` load-bearing. It still matters in the
gap between the two, so a test now makes `lstat` report a directory for an entry
that is really a link out of the home — and the probe fails. `survey-ignores-types`
also passed, and that one was genuinely redundant: a non-directory fails the
`O_DIRECTORY` open below it either way. **Removed and recorded rather than
counted** — the check stays so the right code is reported for the right reason,
but the probe proved nothing.

**Three evidence corrections.** An `inventory` comment still called the
`0o600`/stat seam the observed operator shape; the observed result is
`opendir:EACCES` on a runtime-owned `0o700` directory. My summaries said **94**
tests where the bound log said **95** — the count I kept discounting was the
audit case, which passes once the manifest is rebound. And, found while fixing
those, **the operator packet's command still advertised manifest `3b0020ba`**,
from before R1–R3: I appended the 182771 section without moving the two command
lines with it. Every earlier digest is refused, so the stale line could only have
produced a refusal rather than a wrong run — but a packet naming bytes that are
no longer the candidate is exactly the drift the digest exists to prevent.

Preserved: verified R3, turn-2 no-op, the restored `0o660` contract, complete
structure refusal and every strict contract. No live run, fresh identity,
consumed-root repair, private-tree inspection, product expansion or model-policy
change. Both identities stay consumed; G1 unqualified; W161234/C1/C2 independent.

## Claim 183114 — the fresh run identity

Review182947 accepted candidate182906 **for the offline fixture correction only**
— not live qualification, not a rerun of a consumed identity. Owner183105
selected a fresh unused identity and a newly digest-bound packet. All four
accepted inputs revalidated before any edit.

**The identity is `183114`.** Two are now consumed and neither is reusable:
`178579` by the initial-artifact failure and `180078` by the collection failure.
All six of their roots keep their original timestamps, and the unaddressability
test now applies to **both** names and to the worker as well as the fixture and
contract. The three fresh roots were confirmed free and **none was created** —
this reserves nothing and launches nothing.

**Three files changed**; `qualification_contract.py`, `qualification_worker.py`
and `verify-offline.py` are byte-identical to the accepted candidate, so the
whole R1–R3 correction carries over untouched.

**The packet states what a run would and would not settle**, because the
acceptance answers none of it:

- **The model stays unqualified, and cannot be settled by any fixture change.**
  Run180078's `modelUsage` held exactly two keys, one of them the expected model,
  with no direct `model` member. The other key is **unrecoverable** — the raw
  terminal document is read from an anonymous bounded pipe and never retained.
  Retaining more is a separate selection with its own privacy question, and the
  predicate is not relaxed here.
- **G2/G3/G5 are unobserved**: no `--resume` turn has ever run, so restoration
  from a manager-rebuilt home is still the thing this campaign has never done.
- **G4/G6** have one observation each, from turns that never reached a second arm.
- **The custody correction is offline-verified, not field-verified** — same-UID
  synthetic fixtures only, with no two-UID or live-provider observation behind
  it. That is what a `183114` run would put under load first, and saying so is
  more useful than letting the acceptance imply more than it covers.

**Verification: 98 tests, OK, 0.3638466850388795 s**, exit 0, no timeout, owned
process group positively absent. **Thirty-one reversal probes**, each failing
where it should — `identity-back-to-consumed` was split so there is one per
consumed identity, since a rule about two names needs two probes.

No live execution, production enabling, root reservation, fixture launch,
consumed-root repair, marker reset or model-policy change.

## Claim 183197 — publication diagnostics after run183114

Run183114 failed at first turn with `publish-shape` **and nothing else**, after
the provider started and exited. Owner pass183193 selected the offline correction
cycle. Both defects it exposes are mine, and both are the shape this campaign
keeps finding.

**One code stood for seventeen checks.** Bounds, traversal failures,
credential-link and name checks, type checks, project and session shape,
ownership, alias and the chmod all refused as `publish-shape`/`publish-type`, so
the export could say a run refused and not which question it answered — exactly
what `unclassified` did one layer down, reintroduced by me one layer up. Every
refusal now names its check from a closed vocabulary with a closed errno, and an
unlabelled refusal degrades to `other` rather than leaking anything.

**A later failure discarded an observation already made.** `publish` ran *before*
`c.projection`, so a publication refusal threw away a provider exit and terminal
record that were already available — run183114 cannot say whether the provider's
answer was even well-formed. The observation is made first now and carried
through. **Evidence, not a pass**: the arm still fails, no second arm is
admitted, no gate is bypassed, and a preserved observation is validated exactly
like a real terminal record so a forged one cannot ride in.

**Verification: 109 tests, OK, 0.3638401919743046 s**, exit 0, no timeout, owned
process group positively absent. **Thirty-six reversal probes**, each failing
where it should.

**Two probes found a real coverage gap.** `observe-after-publishing` and
`drop-the-preserved-observation` **passed** at first: the FakeEngine builds its
own failure record, so nothing exercised the real `worker.main` ordering at all.
Two tests now drive the actual entry point, and both probes then failed. While
writing that harness I also mocked `invoke` without firing its `started`
callback, so `provider_started` read False for a provider that had in fact
started — I made the mock faithful rather than weakening the assertion.

**What the next run could distinguish, and what stays unknown.** A future run
would name the exact publication branch and its errno, and say what the provider
answered even when publication refuses. It would **not** explain run183114: that
export cannot identify the branch and no synthetic reproduction recovers its
cause. The model stays unrecoverable for the earlier runs, G2/G3/G5 are still
unobserved with no `--resume` turn ever run, and the custody correction remains
same-UID synthetic evidence only.

All three identities stay consumed; an old manifest is not rerunnable because the
diagnostics improved. R1/R2/R3, turn-2 `0o660` and every strict contract
unchanged. No live run, private-tree inspection, fresh identity or consumed-root
repair.

## Claim 183267 — one validator, and the last unwrapped operation

Review183243 withheld the previous candidate on two findings. Both are mine.

**Two validators for one record.** The failure path carried a *shorter copy* of
the terminal check, so `type`, `subtype`, `is_error`, `session_matches`,
`unknown_member_hashes` and `api_error_status` went unverified **on that path
only** — a canary in any of the six was refused on the normal path and exported
on the failure path, six times out of six. The run still failed and no second arm
was admitted, so it was a closed-export defect rather than a false qualification;
but the export is the product, and I introduced the second copy myself last turn
when I added the preserved observation. There is now one `valid_terminal` used by
both paths, and each field is tested on **both** — paired, because the defect was
precisely that the two paths disagreed.

`valid_publication` also checked membership before type, so an unhashable `check`
or `errno` raised `TypeError` *out of* the validator instead of being refused by
it. Types are checked first now.

**The target's own metadata read had no wrapper.** An `EACCES`/`EIO`/`ENOENT`
from the `fstat` in `_mutable` escaped as `unclassified` with a null publication
diagnostic — the one operation left in the publication path still able to lose
its own cause, which is exactly what this cycle exists to prevent. It reports a
`target-metadata` check now, and `home-open`, child `open` and `chmod` each got
their own actual-operation coverage.

**Verification: 114 tests, OK, 0.3638996609952301 s**, exit 0, no timeout, owned
process group positively absent. **Thirty-nine reversal probes**, each failing
where it should. Two probes — `no-consistency-guard` and
`accept-a-forged-observation` — targeted lines the shared validator replaced;
I moved them to where the guard now lives rather than dropping them, since the
property is still real even though the line moved.

I also added the case that keeps the correction honest: a **valid** observation
still survives on the failure path. Tightening a validator is easy to overdo, and
throwing the good case out with the bad would have quietly removed the evidence
this cycle was meant to preserve.

These probes do not recover run183114's cause — that export cannot identify the
branch. All three identities stay consumed. Retained descriptors,
before-mutation refusal, turn-2 `0o660` and every strict contract are unchanged.

## Claim 183316 — completing the shared total validation

Review183295 verified the six-field leak and the `target-metadata` diagnostics
fixed, and left one bounded continuation. It is the same fault again, in the
validator I did not look at.

`valid_terminal` built sets from unvalidated `members`/`model_fields` elements,
and `consistent` compared untyped model diagnostics by membership. `set([{}])`
raises `TypeError` on an unhashable element, so eight shapes JSON permits —
`members=[{}]`, `[None]`, `model_fields=[{}]`, `[1]`, `model_diagnostic` as a
list or null, `model_usage_diagnostic` as a dict or null — raised **out of** the
validator and surfaced as `unclassified`. The normal path never said
`terminal-record-values`; the preserved path never said `worker-failure-shape`.

**This is exactly the fault I fixed in `valid_publication` last turn and did not
carry across.** Fix-the-case-not-the-class is the mistake this review cycle has
now caught in me three times — R1/R2 at 182906, the shorter validator at 183267,
and this. Element and diagnostic types are now checked before any set
construction or membership test, in **both** predicates, with the tests paired
across both paths.

No canary was exported and no second arm was admitted, so this was diagnostic
completeness rather than a renewed leak — but a failure the export cannot name is
precisely what this cycle exists to remove, so it is not a small point.

**Verification: 116 tests, OK, 0.3637980869971216 s**, exit 0, no timeout, owned
process group positively absent. **Forty-one reversal probes**, each failing
where it should.

Everything the review asked to preserve is preserved: the verified six-field
refusal, the list/dict/null publication refusals, the actual `worker.main`
EACCES/EIO/ENOENT `target-metadata` causes, a valid retained observation, the
failed-arm and no-second-turn gates, retained descriptors, before-mutation
refusal, turn-2 `0o660`, the strict contracts, the image and the limits.
Run183114's cause remains unrecoverable and all three identities stay consumed.

## Claim 183372 — the fourth identity, bound to one diagnostic experiment

Review183339 accepted candidate183316 as complete for the offline cycle — no
implementation correction remains. Owner183369 selected a fresh digest-bound
identity and packet for one diagnostic qualification experiment. All four
accepted inputs revalidated before any edit.

**Identity `183372`.** Three are consumed: `178579` (initial artifact), `180078`
(collection), `183114` (publication). All nine roots keep their timestamps, none
is repaired, and the unaddressability test and probe set now cover all three
names. The fresh roots were confirmed free and **none was created**.

**Two outcomes, both worth having.** Run183114 refused at `publish-shape` and the
export could not say which of seventeen checks answered; the accepted cycle fixed
exactly that. So this run either names the actual publication check with its
closed errno **and** retains the validated terminal observation — a publication
failure that finally says what the provider answered — or publication succeeds
and it reaches restoration, which would be the first `--resume` turn this
campaign has ever run and the first evidence for G2/G3/G5.

**A failure that names its branch is a result, not a wasted run.** That is what
the owner-confirmed cycle was for: stop rerunning until failures produce useful
information, then run once. I have written the packet to say that plainly, rather
than presenting the run as likely to succeed.

**What it cannot do**, also in the packet: it cannot recover run183114's cause,
since no later run explains an earlier one; it cannot settle the model, which is
unrecoverable from a document never retained; and it is the first test of the
custody correction outside same-UID fixtures, which is precisely why a
publication failure here would be informative rather than disappointing.

**Verification: 116 tests, OK, 0.3638261739979498 s**, exit 0, no timeout, owned
process group positively absent. **Forty-two reversal probes**, each failing
where it should.

Preserved: the strict model/artifact/continuity acceptance, the image, the
two-turn shape and limits, retained descriptors, before-mutation refusal, the R3
collection diagnostics and turn-2 `0o660`. No agent live execution, root
reservation, fixture launch, consumed-root repair, model-policy change or
production enabling.

## Claim 183524 — publish traversal, not contents

Run 20260916T035035Z published, consumed shutdown, then refused at
`source-inventory` with `state-coverage-incomplete`, cause **EACCES**.

**The diagnostics paid for themselves.** Run183114 said `publish-shape` and
nothing else; this one named its step, its refusal and its errno and carried the
provider's answer. That is what made the real problem visible.

**The problem is structural and it is mine.** Publication relaxed two objects
while `inventory` demands whole-HOME name and type coverage under a different
uid. Those cannot both hold over a home whose other directories the CLI creates
`0o700`. I built each half against its own review and never checked them against
each other — the same class of mistake as the two validators, one level up.

**The resolution.** Name and type coverage needs `r-x` on directories and `r` on
no file: `scandir` needs read on the directory, `entry.stat` needs search on it,
and neither opens a file. So every runtime-owned directory becomes `0o2750` —
setgid kept, no world access — and every file keeps the mode the CLI gave it
except the one selected session at `0o640`. Not a broad HOME chmod: no file
content becomes readable that was not already, nothing is skipped, nothing extra
is copied, and no gate moves. Directories are published only if the runtime owns
them. All mode changes still follow the complete preflight on descriptors the
survey opened, bounded by a `directory-bound` check rather than by the fd limit.

**Verification: 120 tests, OK, 0.36381306999828666 s**, exit 0, no timeout, owned
process group positively absent — including the observed shape end to end: the
runtime-private directory that used to refuse now inventories, the subset copies,
the second turn is reached, and the private file inside it stays unreadable and
recorded rather than skipped. **Forty-six reversal probes**, each failing where
it should.

**One probe found a gap.** `publish-file-contents-too` **passed**: same-UID
fixtures cannot express "not runtime-owned", so nothing proved the ownership gate
load-bearing. A test now makes `lstat` report a foreign uid for one directory and
asserts it is left alone while the runtime's own are published.

**Same-UID limits, labelled rather than glossed.** "Unreadable to the manager" is
stood in for by mode `0o000`, and "owned by someone else" by a targeted `lstat`
report. Both are named as stand-ins. Same-UID mode assertions are not evidence of
manager readability and I have not claimed otherwise.

**The model gap is untouched.** `expected-plus-other` with two keys was observed
**again** and strictly refused; the other key is unrecoverable. No model policy
or retention change. This is a custody correction, not model or production
qualification.

**One thing worth flagging:** a direct identity preparation moved the fixture to
`20260916T035035Z` between claims and rewrote the identity comment — which broke
a test of mine that asserted the *prose*. I kept the real property
(unaddressability of executable text) and moved the history assertion to the
manifest's `consumed_identities`, which is evidence rather than someone else's
wording. All five identities are consumed, so this manifest is **not** rerunnable
authority; a future live run needs its own selection and a fresh identity, which
this cycle does not prepare.
