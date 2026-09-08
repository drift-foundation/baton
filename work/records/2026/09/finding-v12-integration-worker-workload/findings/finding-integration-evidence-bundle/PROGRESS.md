# Progress

## 2026-09-07 — baton.claude — claim112654, the bundle producer and its contract

Adopted this record, pinned the exact interface in FINDING.md before writing
code, and implemented all four assigned paths. Handed back for independent
review; the one thing this turn does not prove is named at the end rather than
left for the reviewer to discover.

### Revalidation before acting on any pinned decision

All thirteen source hashes in
`../../evidence/revalidation-112610/baseline.json` re-measured against the
current tree: **thirteen of thirteen match**. The three assigned new paths were
absent, as that record says. Nothing in the parent's proposal was acted on
without that check, and the two places where the proposal could not be
implemented as written are recorded as changes in FINDING.md rather than
applied silently.

### What was built

`v12/worker/integration_contract.py` — standard-library only. The fixed
`/input/source` layout, the closed `baton.integration-input/1` envelope, the
bounded no-follow readers, the provider report's closed shape, and the outer
assignment/result names mirrored from `integration.runtime`. Its whole import
list is `json`, `os`, `stat`, and a subprocess with `sys.path` set to the
worker directory alone proves it imports no `baton_v12`, `tools` or
`source_profiles` module.

`v12/python/tools/integration_bundle.py` — the manager-side producer. It
re-resolves every fact through its accepted owner, refuses disagreement before
anything consumable exists, reads the retained objects through
`--no-optional-locks` `rev-parse`/`ls-tree`/`cat-file` and nothing that writes,
and publishes under a staging name that is renamed into place only once every
byte is written and read-only.

`v12/python/tests/tools/test_integration_bundle.py` and exactly one additive
`tools/parallel_test.py` entry. No existing registry member moved.

### Two defects the real owners found in my own reader

Both are the same shape as the one I shipped in W112029, and both were caught
because the manager half of this suite is not seamed.

**The Job store answers `test_scope` as TEXT, not as a parsed list.** My first
reader treated the column as already parsed and refused every genuine Job with
"an accepted Job's test scope is an array". `admission._job_for` parses it with
`json.loads`; this now parses it the same way and builds the scope through the
same `check_relative_path`, so the digest it compares is computed by the same
rule that produced `scope_digest`.

**`identity-mismatch` is not an `integrity` code.** The closed pairing rejected
my refusal at the moment it fired. It is `runtime-observation/identity-mismatch`,
which is the pairing `review_cycles` already uses for the same question.

### Two recorded changes to the proposed contract

**`MAX_PATHS` is 512 and not the proposed 4096.** `contracts.canonical` freezes
an array at 512 members and every digest in this build goes through it, so a
4096-row path table could not be canonicalized, therefore not digested,
therefore never published or read back. The measurement is in the code and one
case asserts the bound is reached before any digest is attempted. Every other
proposed bound is adopted unchanged.

**`MAX_EVIDENCE_BYTES` (1 MiB per projection) is added**, because the proposal
bounded everything except the evidence documents and an unbounded document is
an unbounded allocation.

### The decision about the launch, and why

The bundle carries the launch document's **digest** and never the document. Its
`session` is a live control-API credential, and copying it into material
mounted read-only for the whole runtime would widen that secret's blast radius
for nothing: a workload can still prove the launch it was handed is the one the
bundle was made for. `test_no_live_session_token_reaches_the_bundle` walks every
published byte and asserts the token appears in none of them.

### How this is proved, and the one thing it does not prove

The manager half is **not seamed at all**. `TheProducerComposesFromRealOwners`
drives the real `_OrdinaryAdmissionWorld` — a real worker turn whose command
really runs, real custody through freeze, intake, retention and cleanup, real
Authority sessions writing the three policy receipts, a real accepted
checkpoint and a real Job store — imported from its own suite and never edited.
The envelope's eligibility is compared against a live `resolved_account` call,
the evidence projections against the public readers' own answers, and the
published bytes are re-measured off disk and compared with the returned
manifest and bundle digest.

The version control **is** a seam: a deterministic read-only runner over real
temporary files, which is the methodology the parent finding fixes for this
producer ("use deterministic read-only Git-runner seams and real temporary
files; do not mutate Git merely to create a reviewer fixture"). The seam parses
each question and then proves the argv it was handed is the vector the module
composes for those exact operands, so a vector that drifted would stop being
answered rather than being met by a fake taught the new shape at the same time,
and the four composed vectors are asserted word for word.

**What that leaves unproved, plainly: no `git` process is executed anywhere in
this suite.** Nothing here establishes that a real `git` binary answers those
four vectors in the shape the seam assumes — the `ls-tree -z` record layout,
`cat-file -s`'s trailing newline, or `--no-optional-locks` being accepted in
that position. That is the same limitation `checkpoint_profiles`' own injected
runner carries, and I am not describing the seam as more than it is.

One fixture attribute is patched and it is named here: the accepted world's
checkpoint profile is a manager-side fake standing in for
`GitCheckpointProfile`, answering the real object names a real repository
holds; its `name` alone says "reference". `mock.patch.object` sets that one
attribute to the Git profile's for the duration so the line row, checkpoint row
and sealed evidence agree on the profile a Git deployment configures. No
behaviour is replaced, the file is not edited, and the producer's own rule —
that it reads Git checkpoints and refuses any other profile — is driven
unpatched by `test_evidence_of_another_profile_or_another_shape_refuses`.

### Verification

`tests.tools.test_integration_bundle` — **55 passing, 0 failures**, 2.0s. Every
test name is unique; the class breakdown is 16 + 12 + 12 + 6 + 5 + 4. The real
admission world is composed inside `setUp` from a method-local import, so no
`TestCase` is bound at module level and no suite is inherited — the two
inflations I introduced earlier in this campaign are avoided deliberately.

`tests.tools.test_parallel_runner` — 36 tests, **one error, unchanged from the
baseline measured with my registry entry removed**. My module registers
cleanly. The error is a pre-existing gap reported below.

**Canonical subtree gate: 4885 tests in 248.0s, 11 failures, 1 error, 21
skipped**, retained at `evidence/implementation-112654/subtree-gate.txt`.
Handed over red with the **distribution unchanged**: six boundary-inventory,
four live-engine cleanup, one authority-catalog, one registry error. No new
failure and no new diagnostic. Neither new source file appears anywhere in the
gate's output — the boundary inventory scans `src/baton_v12` and not `tools/`,
so this addition creates no inventory entry.

The previous figure I recorded at the W112029 handoff was 4815. Fifty-five of
the seventy new tests are mine; the other fifteen arrived in the tree between
the two runs from Work that is not mine, and I did not attribute them further.

### Operational finding — not mine to fix

`tools/parallel_test.py` registers neither `tests.integration.test_driver` nor
`tests.job_manager.test_review_driver`. `test_parallel_runner`'s own guard
fails on exactly those two, and it fails identically with my entry removed, so
it is pre-existing. It means the registry-driven runner does not execute those
two suites, though the canonical subtree `discover` gate does. My assignment
authorizes exactly one additive registry entry, so I have not added theirs.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_contract.py` | `48a83cbaff533174baf0f98a6d468f27161c8e0f09d08705a9cdfbb065362a96` |
| `v12/python/tools/integration_bundle.py` | `06888022bb76798557825a87886f4e22269c0e0d0af1c67136e5aa26bdc6931d` |
| `v12/python/tests/tools/test_integration_bundle.py` | `3fe32c4414702c5ec587f7216e302657083bddb58e8bf900c176fe7e6df2ac8a` |
| `v12/python/tools/parallel_test.py` | `1ae0956fda4bfdb8242c8f5e0a57e7c7dd3833904042dfc7734fc0acfecc16f4` |

No worker entry, workload, recipe, lifecycle, integration core, OCI, Authority
or shared serving path was touched. `tests/integration/test_driver.py` and
`tests/job_manager/test_review_driver.py` are imported and read and are
byte-identical. No Git operation of any kind was performed, in this repository
or anywhere else.


## 2026-09-07 — baton.claude — claim112902, the three P1 corrections

Adopted `review-2026-09-07T19-29-28Z.md`. All three findings are real, all
three are corrected, and I reproduced each one against my own bytes before
changing anything. The four reviewed hashes still matched the tree when I
claimed, so the bytes I corrected are the bytes that were reviewed. Scope
unchanged: the same two sources, the same test module, the same one registry
entry, which is byte-identical to what the review already checked.

### The reviewer's own three reproductions, re-run against the correction

`evidence/correction-112902/reprobe.py` performs the review's exact seams and
records what each boundary now answers; `reprobe.json` is the result and
`reviewer-probe-rerun.txt` is the reviewer's unmodified `probe.py` failing at
its first assertion because the behaviour it asserts no longer exists.

| reproduction | now |
| --- | --- |
| symlinked `evidence/` through `read_bundle` | refuses: not a directory of its own inside the bundle |
| symlinked `blobs/` through `bundle_blob` | refuses, same boundary |
| symlink naming the whole bundle root | refuses: the root is not openable without following a link |
| line directory replaced during extraction | refuses `runtime-observation/identity-mismatch`; no destination, no staging |
| 252 two-sided edits (513 files) | refuses at 252 reviewed paths against the bound of 251; nothing published |
| 251 two-sided edits (511 files) | publishes, 511 manifest entries, digest matches, consumer accepts |

### P1 one — every component, not just the last

`O_NOFOLLOW` on a whole pathname rejects only the final component. I pinned an
every-component boundary in the FINDING and did not implement one, and the
reviewer is right that a valid content digest establishes nothing about path
custody: all three symlink substitutions read back with correct hashes.

The reader now opens the root with `O_RDONLY | O_DIRECTORY | O_NOFOLLOW`,
descends each interior component with the same flags **relative to the
descriptor above it**, and opens the file with `O_NOFOLLOW | O_NONBLOCK`
relative to its proved parent. Nothing is re-resolved by name after it is
proved, so there is no lstat-then-open window — the reviewer asked for that
explicitly. `read_bundle`, `bundle_blob` and `read_assignment` all go through
it. Public signatures are unchanged; `open_bundle_root` is added and exported
because the traversal starts somewhere and hiding that made the first version
easy to get wrong.

### P1 two — looking again after reading

`compose_bundle` nominated the line once, before the version-control reads, and
never looked again. It now re-resolves the complete account, checkpoint, line
and all seven evidence projections after extraction, compares them member for
member, and nominates the line directory a second time. Any drift refuses with
no consumable destination.

**One thing I built and then removed, because it cannot fail.** My first
correction also held a directory descriptor open across the extraction and
re-`fstat`-ed it at the end. That check can never fire: an open descriptor
names one inode for as long as it is open, so it answers the same identity
whatever happens to the NAME. The reviewer's own substitution proves it — the
descriptor still matched and the second NOMINATION is what caught the swap. A
check that cannot fail reads like protection and is not, so it is gone and the
FINDING pin is corrected to say what is actually there.

This is a detection boundary and not a binding, and I would rather say so than
imply otherwise: the runner is handed a pathname and nothing here stops that
name being re-pointed for a subprocess. What is guaranteed is that no bundle is
published over a source or an account that stopped agreeing with the one this
producer proved. W110774's grant check stays its own obligation.

### P1 three — every answer before publication

The rename was second and `digest(manifest)` was first-after, so a manifest
that could not be represented refused **after** a complete consumable bundle
existed — with no digest returned and a retry that collided with the wreckage.

Publication now writes to staging, measures every staged file by reading it
back, computes the manifest digest and the envelope digest, and only then
renames. Anything that refuses discards the staging tree, so a retry is
unobstructed and one case drives exactly that.

**And the bound is now derived rather than chosen.** `MAX_BUNDLE_FILES` is 512
because the manifest is one canonical array; nine files are fixed and an edit
emits at most two blobs, so `MAX_PATHS = (512 - 9) // 2 = 251`. My first
correction of the proposed 4096 stopped at 512 and had the same cause as the
mistake it was fixing — I applied the canonical member bound to the path table
and not to the manifest that table produces. One case asserts the derivation
itself rather than restating 251, so the two cannot drift apart again.

`_publish`'s file-count guard is a backstop the derived path bound makes
unreachable through the public entry, and the overflow case says so rather than
pretending it is the gate that fires.

### The two reconciliations

The producer totalled unique blob content and the reader summed every side
reference, so a blob shared by two rows was counted twice on one side of the
boundary and once on the other. The reader now totals per unique content
address and refuses two rows that declare different byte counts for one
address. And `MAX_EVIDENCE_BYTES` — declared in both spellings and enforced
nowhere — is now checked where the projections are emitted.

### Verification

`tests.tools.test_integration_bundle` — **72 passing, 0 failures**, 3.7s. That
is the 55 from claim112654, every one preserved and unchanged in meaning, plus
17: five traversal cases through all three public readers, two bound-derivation
and blob-accounting cases, four drift cases with their unchanged-world control,
and the exact-maximum, first-overflow, retry and evidence-ceiling cases.

`tests.tools.test_parallel_runner` — 36 tests, one error, the same pre-existing
registry gap reported at claim112654 and unchanged by this correction.

**Canonical subtree gate: 4902 tests in 251.7s, 11 failures, 1 error, 21
skipped**, retained at `evidence/correction-112902/subtree-gate.txt`. Handed
over red with the **distribution unchanged**: six boundary-inventory, four
live-engine cleanup, one authority-catalog, one registry error. The count moved
by exactly the 17 tests added here. No new failure and no new diagnostic.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_contract.py` | `29e64f0bbd66ef03cec0816c9bc4be5d6064633a315381ba73b460a0175a09d0` |
| `v12/python/tools/integration_bundle.py` | `e75c551007fd9ac4c35cf67ed6fd4aab8236dcac0c751258da5c06d1d951808f` |
| `v12/python/tests/tools/test_integration_bundle.py` | `a74733983d927474b92b26f5bea0360143f2088ba491334460d5791f16548095` |
| `v12/python/tools/parallel_test.py` | `1ae0956fda4bfdb8242c8f5e0a57e7c7dd3833904042dfc7734fc0acfecc16f4` (unchanged) |

The registry file is byte-identical to the one the review checked. No
production core, parent workload, lifecycle, OCI, Authority or shared serving
path was touched. `tests/integration/test_driver.py` and
`tests/job_manager/test_review_driver.py` are imported and read and are
byte-identical. The reviewer's retained evidence under `evidence/review-112857/`
is unmodified. No version-control mutation of any kind was performed.

### Still true from claim112654, and still stated

No `git` process is executed anywhere in this suite. Nothing here establishes
that a real `git` binary answers the four composed vectors in the shape the
deterministic read-only seam assumes. The review confirms real Git command
interoperability remains unproved and I am not claiming otherwise.


## 2026-09-07 — baton.claude — claim113036, the second correction round

Adopted `review-2026-09-07T19-51-54Z.md`. All three remaining findings are
real, all three are corrected, and one of them corrects a claim I made in this
dossier — which I withdraw explicitly below rather than quietly restating. The
four reviewed hashes still matched the tree when I claimed. Scope unchanged:
the same two sources, the same test module, the same registry entry, which is
still byte-identical to the one the review checked.

### The claim I withdraw

The previous entry said the correction "guarantees that a bundle is never
published over a source that stopped agreeing with the one this producer
proved". A before-and-after pathname check does not establish that, and the
review's transient-swap probe shows exactly why: a substitution restored before
the second nomination leaves both measurements agreeing and publishes.
Review112857 asked for the reads to be BOUND and I answered with detection, then
described the detection as if it were the binding. Withdrawn, and replaced by a
binding rather than by a better sentence.

### The reviewer's own three reproductions, re-run against the correction

`evidence/correction-113036/reprobe.py` performs their seams; `reprobe.json` is
the result.

| reproduction | now |
| --- | --- |
| `read_bundle(alias)` | refuses: `'alias'` is a link |
| `read_bundle(alias + "/.")` and `bundle_blob(alias + "/.", side)` | refuse: a root has one canonical spelling |
| root reached through a symlinked ancestor | refuses; the same material by its own name still reads |
| one 5-byte blob shared by two rows under a scaled bound of 8 | publishes, **one** content read, reader accepts |
| transient swap restored before the later check | all 6 reads bound to the line's own identity, no command named the pathname, published from the proved directory |

### P2 — the root is traversed now, not opened

Opening the root pathname whole left two ways through: an ancestor link was
ordinary kernel traversal, and `alias + "/."` moved the link out of the final
component so `O_NOFOLLOW` never saw it. My source comment excused the root's
ancestors as fixed mount points, which narrowed a requirement I had already
written down — and the root is a caller-supplied operand whatever the deployment
mounts.

`open_bundle_root` now requires one canonical absolute spelling with no empty,
current or parent component and no doubled leading separator, then walks from
the filesystem root opening one component at a time, each `O_DIRECTORY |
O_NOFOLLOW` relative to the descriptor above it. `realpath` is deliberately not
used: it resolves the link and hands back the target, which accepts the bypass
instead of refusing it. The interior reads are unchanged.

### P1 — the extraction is bound to a descriptor

The runner contract changed shape and is pinned in FINDING.md:
`runner(argv, *, directory)`, where `argv` carries no repository pathname and
`directory` is an open descriptor the command must run with as its working
directory, valid for the duration of that call only. The four vectors lost their
repository operand and `reviewed_path_table` takes the descriptor.

A pathname is resolved again on every use, so `-C <path>` asks the kernel a
fresh question each time and a rename between two reads changes the second
answer. A descriptor names one inode for as long as it is open, and the name is
no longer part of any command. The producer proves the directory once —
`nominate_source` against the manager's recorded row, then `fstat` on the
descriptor it opened, which closes the window between proving and opening — and
every read goes through it.

**What it still does not claim.** This module cannot audit what an injected
runner does with the descriptor; the contract is what a deployment owes. The
post-extraction nomination and the complete owner re-resolution are KEPT because
they answer a different question, and neither one is the binding.

### P2 — shared content is charged once

`_content` charged the remaining unique budget before the content address was
known, so a blob two rows share was read twice and could refuse as oversized
while adding nothing — the producer refusing input its own reader accepts. Reads
are now cached by the retained OBJECT identity, which determines content
exactly, so a second reference costs no command and no bytes. Size and content
verification on the first read is unchanged, and two objects that address one
content with different bytes refuse.

One adjacent thing the scaled probe exposed: the envelope's instruction
reference was bounded against `MAX_BLOB_BYTES` rather than
`MAX_INSTRUCTION_BYTES`, two bounds tangled where only one applies. Corrected.

### The eleven changed test methods, and my under-count

I wrote "four" in the pin and the measured answer is **eleven**: I counted the
methods that call `reviewed_path_table` or assert the vectors and forgot the
refusal cases, which seed their answers keyed by those same vectors. The
comparison against the reviewed candidate is retained at
`evidence/correction-113036/test-methods.json`: **72 before, 83 after, 0
removed, 11 changed, 11 added**. Every change is the same mechanical move — a
vector call losing its repository operand, or a path becoming a descriptor. No
subject changed and no assertion was weakened; the two vector cases gained
assertions that no composed command carries `-C` or the repository pathname.

### Verification

`tests.tools.test_integration_bundle` — **83 passing, 0 failures**, 4.7s.

`tests.tools.test_parallel_runner` — 36 tests, one error, the same pre-existing
registry gap reported at claim112654 and unchanged here.

**Canonical subtree gate: 4913 tests in 267.3s, 11 failures, 1 error, 21
skipped**, retained at `evidence/correction-113036/subtree-gate.txt`. Handed
over red with the **distribution unchanged**: six boundary-inventory, four
live-engine cleanup, one authority-catalog, one registry error. The count moved
by exactly the 11 tests added. No new failure and no new diagnostic.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_contract.py` | `03e346c27b6b919f00581183e301b9c5c979e89ba43adb29aa301d0ce9e735a6` |
| `v12/python/tools/integration_bundle.py` | `ee7a41f545c4cf8806af31d55e318f5a256efb2b525081b118d82ad4fb8c5c20` |
| `v12/python/tests/tools/test_integration_bundle.py` | `645b16f533530d108c0824d48267319b28d0bf7df001b0625c3be56523629c26` |
| `v12/python/tools/parallel_test.py` | `1ae0956fda4bfdb8242c8f5e0a57e7c7dd3833904042dfc7734fc0acfecc16f4` (unchanged) |

No production core, parent workload, lifecycle, OCI, Authority or shared serving
path was touched. `tests/integration/test_driver.py` and
`tests/job_manager/test_review_driver.py` are imported and read and are
byte-identical. Both retained review evidence directories are unmodified. No
version-control mutation of any kind was performed.

### Still true, and still stated

No `git` process is executed anywhere in this suite. Nothing here establishes
that a real `git` binary answers the four composed vectors in the shape the
deterministic read-only seam assumes — and the seam now runs with a descriptor
rather than a `-C` operand, so a deployment's runner must honour the
`fchdir` contract for the binding to be real in production. The review records
real Git command interoperability as unproved and it remains so.
