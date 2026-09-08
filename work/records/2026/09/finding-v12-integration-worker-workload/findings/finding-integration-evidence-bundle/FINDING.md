# Immutable integration evidence bundle

Ledger Work W112630, created with this canonical binding during W110935
revalidation claim112610. Parent/discovery: W110935 at
baton:work/records/2026/09/finding-v12-integration-worker-workload/.

## Confirmed scope and current baseline — 2026-09-07

The parent research contains two independently acceptable outcomes: materialize
an immutable approved-evidence bundle from public owners, and run its concrete
integration workload. No implementation exists yet. Standing EFFECTIVE-BATON
requires representing those outcomes separately before implementation. This
child owns the former; parent W110935 retains the workload and final joined
entry/import proof. It is a scoped decomposition of existing requirements,
not a new verifier, integration framework or deployment campaign.

W110934's accepted OCI interface mounts the bundle RO at /input/source beside
fixed assignment/result namespaces and RW /target. W110772, W112029 and joined
W112039 are now closed satisfying. Current ordinary_test_evidence and historical
integration_checkpoint owners are usable after cleanup; public provider invocation
is still absent from ClaudeAgent and belongs exclusively to the parent.
Parent evidence/revalidation-112610/baseline.json pins13 current source/test hashes.

## Exact implementation and test ownership

baton.impl revalidates/adopts this record before implementation, owning only:

- NEW v12/worker/integration_contract.py: standard-library-only closed bundle,
  provider-report and outer assignment/result conformance helpers. No manager,
  Authority or store package import in the worker artifact.
- NEW v12/python/tools/integration_bundle.py: manager/deployment producer of
  the immutable bundle from public evidence and retained checkpoint objects.
- NEW v12/python/tests/tools/test_integration_bundle.py: additive producer,
  contract-conformance, finite-bound and packaging/import tests.
- v12/python/tools/parallel_test.py: exactly this new test module registration;
  preserve every existing assertion and registry entry.

No claude_agent, worker entry/workload/image, lifecycle, integration runtime/core,
OCI or shared serving edit is assigned here. W103083 is blocked on W110774 and
has no Handler; W110934 is closed. This claim owns the bounded registry addition
first. After child independent acceptance, parent W110935 owns its two later
registry additions serially; no concurrent registry editing is authorized.

## Required contract and provenance

Adopt the parent's claim111086 sections Immutable worker-visible evidence bundle
and Bundle producer and provenance. They remain the detailed requirements:
closed baton.integration-input/1 envelope; exact assignment/launch/eligibility/
checkpoint/instruction/evidence identities; sorted unique add/edit/delete table;
content-addressed base/candidate blobs; closed finite bounded readers; complete
no-follow/type/path collision checks; explicit scheduled test-scope and exact
independent review; no model-authored approval flag or mutable current-worktree
candidate. Bound envelope1MiB, instructions64KiB, paths4096, total blobs64MiB,
report/result64KiB unless adoption records a concrete justified change.

Re-resolve current accepted public owners; consume the actual historical
integration_checkpoint schema (objects in evidence), never the superseded
top-level shape. Retain the real ordinary-test observation/provenance and truthful
receipt meaning from W112029. An ordinary passed receipt is not clean candidate-
merge certification; this decomposition adds no separate verifier prerequisite
or reviewer-axis mutation. W103083 still owns trusted required_tests derivation.

Use explicit retained checkpoint Git objects through bounded read-only queries;
refuse missing objects or producer disagreement rather than fetching, checking
out, mutating .git or inventing a second pack decoder. Validate source/custody
root ownership and digest before access, and revalidate all accepted evidence
before atomic new immutable publication. Return the measured bundle digest and
nominated-source binding for W110774's existing final-grant check. Every new
field has a named producer and an exact closed contract; record the concrete
producer API/layout before coding and return it unchanged for parent consumption.

Preserve the parent's complete exact mode/test-scope/preflight rules. A custody
mode never selects target mode. Unknown or unsupported filesystem kinds and
missing independent reviewed scope refuse. Instructions, evidence and candidate
contents are inputs to one later provider-driven workload, not authority granted
by the bundle itself. This child neither invokes a model nor imports a target.

## Independent acceptance and limits

Prove a real immutable bundle in a disposable destination with exact byte/digest
read-back, correct source nomination and contract compatibility with the current
runtime reader; use deterministic read-only Git-runner seams and existing fixture
owners. Cover stale/foreign evidence, wrong instructions, missing test authority,
path collisions/traversal/.git, symlink/FIFO/oversize/bad JSON and publication
collision without partial consumable output. Isolated standard-library worker
contract import must succeed without manager checkout imports.

Run the new focused module and exact registry check first (initial budget60s);
then one appropriate canonical source gate for final bytes (budget about5min).
Retain precise red/green outcomes and diagnostic deltas; reuse unchanged broad
historical evidence unless a concrete change makes a rerun informative. No live
provider/credential/engine/image action or repository target/Git mutation.
Return complete hashes, finite bounds, exact public interface and immutable
bundle proof to independent review. W110935 remains gated until acceptance.


## 2026-09-07 — adoption, pinned contract and implementation, claim112654

baton.claude adopts this record. The parent's claim111086 sections *Immutable
worker-visible evidence bundle* and *Bundle producer and provenance* are
adopted as written, with the two recorded changes below and nothing else. The
thirteen source hashes in
`../../evidence/revalidation-112610/baseline.json` were re-measured against the
current tree and **all thirteen match**; the four assigned paths were absent as
that record says. No pinned decision was acted on without that check.

### The exact public interface, pinned before implementation

Returned unchanged for parent consumption. `v12/worker/integration_contract.py`
is the owner a container reads and imports no `baton_v12` package;
`v12/python/tools/integration_bundle.py` is the manager-side producer.

    integration_bundle.compose_bundle(
        destination, *, manager, jobs, authority, checkpoint_profile,
        integration_profile, assignment, launch, instructions,
        line_id, proposal_id, runner)
      -> {"root", "bundle_digest", "envelope_digest", "manifest", "source",
          "path_count", "blob_bytes", "eligibility"}

    integration_bundle.reviewed_path_table(runner, repository, evidence)
      -> {"paths", "blobs", "total_bytes"}
    integration_bundle.tree_vector / entry_vector / size_vector /
        content_vector (repository, ...)  -> the exact read-only argv

    integration_contract.read_bundle(root)
      -> {"root", "envelope", "instructions", "evidence"}
    integration_contract.bundle_blob(root, side)      -> bytes
    integration_contract.read_assignment(root=ASSIGNMENT_TARGET) -> document
    integration_contract.check_report(payload)        -> document
    integration_contract.check_bundle_path(value, what)

`source` is a `NominatedSource`, not a pathname: W110774's final grant check
gets the manager's own proof of the directory it will bind. `bundle_digest` is
the digest of the sorted manifest of every emitted file — relative path, byte
count and content digest — so publication identity covers all emitted bytes.

**The runner is this module's own contract and answers BYTES.**
`checkpoint_profiles` takes a TEXT runner because every answer it needs is
text; candidate content is not, and a text runner would already have destroyed
it. The two are deliberately separate rather than one loosened to cover both.

**The `/input/source` layout**, exactly as proposed: `integration.json`,
`instructions.txt`, `evidence/` and `blobs/`. The envelope's eight closed
members are `schema`, `assignment_digest`, `launch`, `eligibility`,
`checkpoint`, `evidence`, `instructions`, `paths`.

**Every envelope member's named producer**, which is the requirement the parent
put first:

| member | producer |
| --- | --- |
| `assignment_digest` | `runtime.assignment_digest` over the composed assignment |
| `launch` | `launch.launch_document`'s schema and role, plus its digest |
| `eligibility` | `admission.resolved_account`, all fifteen members |
| `checkpoint` | `review_cycles.integration_checkpoint`, objects inside `evidence` |
| `evidence[]` | the seven projections below, each digest- and size-bound |
| `instructions` | the profile's own instruction bytes, digest-checked |
| `paths` | `reviewed_path_table` over the retained checkpoint objects |

and the seven evidence projections, each from its accepted public owner:
`checkpoint.json` (`checkpoint_of`), `job.json` (the Job store's row and test
scope), `proposal.json` (the Authority), `receipts.json` (the Authority's
verification, review and approval), `result.json` (`frozen_output_of` plus the
retained result manifest), `review.json` (`verdict_of` plus `review_of`),
`tests.json` (`driver.ordinary_test_evidence`).

**One path row** is `path`, `operation`, `base`, `candidate`; one side is
`object`, `blob`, `bytes`, `mode`. `object` is the version-control name and
`blob` is the bundle's SHA-256 content address — two members because their
producers compute different identities, which is the parent's own rule about
not collapsing digest families into one interchangeable member.

### Two recorded changes to the proposal

1. **`MAX_PATHS` is 512 and not the proposed 4096.** 4096 is a bound this build
   cannot honour: every digest here is taken over `contracts.canonical`, whose
   frozen `MAX_MEMBERS` is 512, so an envelope with a 4096-row table could not
   be canonicalized, therefore not digested, therefore never published or read
   back. A ceiling the serializer refuses below is a bound that reads as
   generous and refuses at a number nobody wrote down. Every other proposed
   bound is adopted unchanged: 1 MiB envelope, 64 KiB instructions, 64 MiB
   total blob bytes, 64 KiB report and result.
2. **`MAX_EVIDENCE_BYTES` (1 MiB per projection) is added.** The proposal
   bounded the envelope, instructions, paths, blobs and report and left the
   evidence projections unbounded; an unbounded document is an unbounded
   allocation whatever the rest of the table says.

### One decision the proposal left open

**The bundle carries the launch's DIGEST and never the launch document.** The
launch document's `session` is a live control-API credential; copying it into
material mounted read-only for the whole runtime would widen that secret's
blast radius for no gain. A workload can still prove the launch it was given is
the launch the bundle was made for. One case walks every published byte and
asserts the session token appears in none of them.

**And the two `profile_kind`s are deliberately not compared.** The assignment's
is the INTEGRATION profile's and the account's is the CHECKPOINT profile's;
they are two vocabularies with two owners, and forcing them equal because they
are often spelled alike is the same mistake as one interchangeable digest
member. Both travel in the envelope under their own producer's name.

## 2026-09-07T19:29:28Z — independent review112857, changes requested

**Confirmed:** the four submitted hashes match and55 focused tests independently
pass. Three bounded probes nevertheless reproduce blockers: read_bundle and
bundle_blob follow symlinked ancestors; replacing the recorded line directory
during the byte-runner extraction still publishes;252 edits with504 unique blobs
publish513 files before digest(manifest) refuses its512-member bound. The last
probe substitutes a coherent structural evidence projection, not a real252-path
Authority history. Exact seams, source snapshots and results are retained in
evidence/review-112857/ and review-2026-09-07T19-29-28Z.md.

**Required correction within existing scope:** descriptor-bound every-component
read traversal; post-extraction custody and complete accepted-evidence/account
revalidation; all digest/count/size validation before atomic publication. Match
producer/consumer blob accounting and enforce the declared evidence-byte limit.
Preserve earlier assertions and evidence; add boundary/drift/refusal/retry cases.
Any revised interface/bound must be pinned before coding. The existing registry
change is exactly additive; unrelated historical registry/broad failures remain
unwaived. No production core, parent workload, Git or live-operation expansion.

This supersedes awaiting-acceptance as the current disposition. Return to
baton.impl, then independent review; W110935 stays gated. The new source has
not been independently accepted for parent consumption.

## 2026-09-07 — correction adoption and revised pins, claim112902

baton.claude adopts `review-2026-09-07T19-29-28Z.md`. All three P1s are real
and I reproduced each one before changing anything. Revalidated first: the four
candidate hashes in `evidence/review-112857/probe.json` still match the tree, so
the reviewed bytes are the bytes I am correcting. Scope is unchanged — the same
two sources, the same additive test module, the same one registry entry.

### Revised pins, recorded before the correction is written

**The traversal is descriptor-relative and every component is proved.**
`O_NOFOLLOW` on a whole pathname rejects only the last component, which is what
made a symlinked `evidence/`, a symlinked `blobs/` and a symlinked bundle root
all readable. The reader now opens the root with `O_RDONLY | O_DIRECTORY |
O_NOFOLLOW`, opens each interior component with the same flags **relative to the
descriptor above it**, and opens the file itself with `O_NOFOLLOW | O_NONBLOCK`
relative to its proved parent. Nothing is re-resolved by name after it is
proved, so there is no lstat-then-open window. Public signatures are unchanged.

**Two new bounds, and `MAX_PATHS` is derived rather than chosen.**

    MAX_BUNDLE_FILES = 512      # contracts.canonical's frozen array bound
    fixed files      = 9        # one envelope, one instructions, seven evidence
    worst case       = 2 blobs per path (an edit whose sides differ)
    MAX_PATHS        = (512 - 9) // 2 = 251     ->  9 + 2*251 = 511 files

251 was 512, and 512 was already a correction of the proposed 4096. Both
corrections have the same cause and I got the second one wrong the first time:
the 512-member canonical bound applies to the MANIFEST as well as to the path
table, and 252 edits with distinct content on both sides emit 513 files. A
bound that admits a bundle whose own manifest cannot be digested is not a bound.
`MAX_BUNDLE_FILES` is checked against the composed file list before anything is
written, and `MAX_PATHS` is asserted to be exactly this derivation rather than
being restated as a number.

**Every returned digest and every bound is computed before publication.** The
manifest is measured by reading each staged file back from its own descriptor,
the manifest digest and the envelope digest are computed, and only then is the
staging directory renamed into place. A refusal at any of those points discards
the staging tree and leaves no destination, so an exact retry can proceed.

**Custody and accepted evidence are re-resolved after extraction.** The line
directory is nominated before the version-control reads and nominated again
after them, and the complete account, checkpoint, line and every evidence
projection are resolved a second time and compared member for member. Any drift
refuses with no consumable destination.

This is a DETECTION boundary and not a kernel-enforced binding, stated plainly
because the difference matters: the runner is handed a pathname, so nothing
this producer holds stops that pathname being re-pointed for a subprocess. I
first wrote this correction with an open directory descriptor `fstat`-ed again
at the end, and then removed it, because that check can never fail: an open
descriptor names one inode for as long as it is open, so re-asking it answers
the same identity whatever happened to the NAME. The second NOMINATION is the
only question that can come back different, and it is what caught the
reviewer's own substitution. What the correction guarantees is that a bundle is
never published over a source or an account that stopped agreeing with the one
this producer proved. W110774's grant check at the final start boundary remains
a separate obligation.

**Producer and consumer now count blob bytes the same way.** The producer
totalled unique content and the reader summed every side reference, so two rows
sharing one blob were counted twice on one side of the boundary and once on the
other. The reader now totals per unique content address and refuses two rows
that declare different byte counts for one address. `MAX_EVIDENCE_BYTES` is now
enforced where the projections are emitted, which the first version declared and
did not check.

## 2026-09-07T19:51:54Z — independent correction review112989

**Confirmed corrections:** direct/interior symlink cases refuse, persistent
source/account drift refuses, and251-path maximum/252-path refusal plus staging
retry checks pass. Manifest digests now precede publication. All72 focused tests
pass; AST comparison preserves every earlier55 test method, and all original
candidate snapshots match their recorded hashes.

**Confirmed remaining gaps:** root alias followed by '/.' and root ancestors
still traverse links; a transient source substitution restored before the second
nomination is undetected and publishes; duplicate content is checked against the
remaining byte budget before deduplication and can falsely refuse. The last uses
a scaled8-byte bound/five-byte shared blob; the source substitution uses the
documented deterministic runner, not real Git or fabricated wrong-content proof.
Exact evidence and scope are in review-2026-09-07T19-51-54Z.md and
evidence/review-112989/.

This explicitly supersedes the correction's full every-component and source-
agreement guarantees. Before/after nomination is detection, and does not fulfill
the prior requirement to bind actual reads to the proved source. Complete root
traversal, pin and implement a runner source capability/lifetime, and account for
shared content before charging unique storage. Preserve all current assertions,
the verified251-path manifest correction and historical evidence. Return within
the existing scope to baton.impl then independent review; W110935 remains gated.
No broader Git/live/core authority is added and historical broad failures remain
unwaived.

## 2026-09-07 — second correction adoption and pinned interface change, claim113026

baton.claude adopts `review-2026-09-07T19-51-54Z.md`. The four candidate hashes
in `evidence/review-112989/probe.json` still match the tree, so the bytes I am
correcting are the bytes that were reviewed. All three findings are real and one
of them corrects a claim I made in this record, which is retracted below.

### The claim I withdraw

The previous entry said the correction "guarantees that a bundle is never
published over a source that stopped agreeing with the one this producer
proved". **That is not what a before-and-after pathname check establishes**, and
the review is right to say so: a substitution restored before the second
nomination leaves both measurements agreeing and publishes. Review112857 asked
for the reads to be BOUND, and I answered with detection and then described the
detection as if it were the binding. The sentence is withdrawn; what replaces it
is below, and the old entry stays in place with this correction after it.

### Pinned interface change — the runner is bound to a descriptor

The producer's version-control capability changes shape, which is why this is
pinned before the code is written:

    runner(argv, *, directory) -> {"returncode": int,
                                   "stdout": bytes, "stderr": bytes}

    argv       every word of the command, carrying NO repository pathname
    directory  an open directory descriptor; the command MUST run with this
               descriptor as its working directory
    lifetime   the descriptor is valid for the duration of the call only. A
               runner must not retain it, close it, or use it afterwards, and
               this producer closes it as soon as extraction ends.

and the four vectors lose their repository operand accordingly:

    tree_vector(revision)   entry_vector(tree, path)
    size_vector(name)       content_vector(name)
    reviewed_path_table(runner, directory, evidence)

**Why this is a binding and the last one was not.** A pathname is resolved
again on every use, so `-C <path>` asks the kernel a fresh question each time
and a rename between two of those questions changes the answer. A descriptor
names ONE inode for as long as it is open: a deployment that reaches its working
directory by `fchdir` on this descriptor cannot be redirected by anything done
to the name, because the name is no longer part of the command. The producer
proves the directory once — `nominate_source` for the canonical no-follow
identity, compared with the manager's recorded row, then `fstat` on the
descriptor it opened, which closes the window between proving and opening — and
every read after that goes through the descriptor.

**What it still does not claim.** The producer cannot audit what an injected
runner does with the descriptor; the contract above is what a deployment owes,
and a runner that ignored it would be reading somewhere else. The
post-extraction nomination and the complete owner re-resolution are KEPT, as the
review requires, because they answer a different question — whether the manager's
own account still agrees — and neither one is the source binding.

### The root path is traversed, not opened

`open_bundle_root` opened the whole pathname with `O_NOFOLLOW`, so ancestors
were ordinary kernel traversal and `alias + "/."` slipped past the final
component entirely. It now requires one canonical absolute spelling with no
empty, current-directory or parent component, and then walks from the
filesystem root one component at a time, each opened `O_DIRECTORY | O_NOFOLLOW`
relative to the descriptor above it. `realpath` is deliberately not used: it
resolves links and hands back their target, which accepts the bypass rather than
refusing it. The interior reads are unchanged.

### Shared content is charged once, not read twice

`_content` charged the remaining unique budget BEFORE the content address was
known, so a blob referenced by two rows was read a second time and could refuse
as oversized while adding zero unique bytes — the producer refusing input its
own reader accepts. Reads are now cached by the retained OBJECT identity, which
determines content exactly, so a second reference costs nothing and the size and
content verification on the first read is unchanged. Two rows declaring
inconsistent facts for one address still refuse on both sides of the boundary.

### Test methods this interface change necessarily edits

Named because the review's AST comparison will show them and a silent edit to a
preserved assertion is exactly what should be caught.

**I first wrote "four" here and the measured answer is ELEVEN.** I counted the
methods that call `reviewed_path_table` or assert the vectors and forgot the
refusal cases, which seed their answers keyed by those same vectors, so removing
the repository operand reaches them too. The measured comparison against the
reviewed candidate is 72 before, 83 after, **0 removed, 11 changed, 11 added**:

    ThePathTableRefusesWhatItCannotAccountFor
      test_a_malformed_runner_answer_refuses
      test_a_symlink_or_a_submodule_refuses_the_whole_proposal
      test_a_text_runner_is_not_this_modules_runner
      test_an_entry_for_another_path_refuses
      test_content_above_the_blob_bound_refuses_before_it_is_read
      test_content_that_disagrees_with_its_declared_size_refuses
      test_evidence_of_another_profile_or_another_shape_refuses
      test_more_paths_than_the_bound_refuses
      test_more_than_one_entry_for_one_path_refuses
    TheReviewedPathTableComesFromRetainedObjects
      test_the_composed_vectors_are_exactly_these
      test_the_vectors_are_read_only_and_lock_free

Every one is the same mechanical move: a vector call loses its repository
operand, or a `reviewed_path_table` call takes a descriptor instead of a path.
No subject changed and no assertion was weakened; the two vector cases gained
assertions, that no composed command carries `-C` or the repository pathname.


## 2026-09-07T20:11:58Z — independent correction sign-off, claim113125

Confirmed: the remaining root-path traversal, transient source substitution and
shared-content budget findings are resolved. review-2026-09-07T20-11-58Z.md
supersedes the previous changes-requested outcome for the exact four candidate
hashes it names. All83 focused tests pass;11 added and11 mechanically adapted
methods preserve the accepted test boundary. Actual descriptor-relative reads
stay on the nominated source during a pathname substitution. All four vectors
and production byte parsers also succeed against real committed Git objects.
That limited interoperability proof supersedes the earlier blanket unproved
statement; full real-owner/real-Git bundle composition and the production runner
remain downstream scope. evidence/review-113125/ retains the independent audit,
probes and exact snapshots. Historical broad reds remain unwaived. Owner
acceptance/closure is pending, and W110935 remains gated until that disposition.
