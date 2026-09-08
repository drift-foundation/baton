# Inspectable import authorization evidence

2026-09-07 — baton.codex, discovered while reviewing W110935 under claim114048.
Ledger: W114085; child of W110935; explicit follow-up to closed W112630.

**Confirmed:** the original workload contract requires the accepted Work/plan's
scheduled existing-test scope, the exact independent review's evaluation of each
changed existing test, and explicit scope for executable additions or mode
changes. Generic approval and candidate path/mode enumeration are insufficient.
This remains the repository policy in AGENTS.md and the parent's FINDING.md.

**Observed:** integration_bundle._job_evidence carries a Job projection with
test_scope and digest identifiers, but no accepted decision text. Its
_accepted_evidence review.json carries the accepted disposition and a frozen
review_result containing findings/log artifact locators and hashes, not those
artifact bytes. Parent evidence/review-114048/mode-scope-evidence.json records
the actual producer output. No executable-mode scope is present in that output.
integration_workload._authorized_scope currently checks only disposition and
test_scope prefix membership. compose_prompt does not require the provider to
inspect the exact accepted decision and frozen review before importing.

**Confirmed:** test_an_edit_preserves_the_reviewed_mode_and_an_executable_one
actually changes a 0644 base to a 0755 candidate in its second case and expects
integration without additional authority. Candidate mode is not permission.
The positive existing-test case likewise tests prefix membership, not inspection
of the independently frozen review's test-change evaluation.

**Decision / allocation:** this is a substantial missing producer capability,
separate from the parent's ending/refusal corrections. Preserve W112630's accepted
history. This follow-up owns only:

- v12/python/tools/integration_bundle.py, especially _job_evidence and
  _accepted_evidence and their public-owner artifact resolution;
- v12/worker/integration_contract.py, worker-visible evidence validation;
- v12/python/tests/tools/test_integration_bundle.py, the bounded evidence tests.

The parent owns integration_workload.py, integration_entry.py and
tests/manager/test_integration_worker.py, including consumption and final joined
proof. Neither child nor parent edits the other's files concurrently. No registry
entry is needed for extending the existing child test module.

**Required result:** a bounded immutable account that gives the worker actual
inspectable accepted decision and independent review evidence, each bound to its
public producer and this exact candidate. It must allow evaluation/enumeration
of every changed existing test and explicit executable/mode-change scope.
Locators alone do not make host evidence readable inside /input/source. Never
invent an approved boolean, convert a generic receipt to permission, or dereference
an arbitrary worker-selected host path. Reuse accepted custody and public owner
readers, finite bounds, no-follow traversal and complete bundle measurement.

**Open implementation choice:** determine the smallest compatible evidence
extension from current public producers. Pin exact fields/bytes, authority owner,
limits and any schema-version consequence here before editing. If those owners
cannot supply an accepted scope or inspectable frozen review, refuse and report
that exact provider gap; do not widen generic core or fabricate a review. The
worker must refuse unsupported/missing authority, with ordinary content-only
positive imports still possible under the original scope.

Acceptance: real accepted owner records to published bundle to worker reader;
exact scope/review bytes and hashes survive; foreign candidate, missing artifact,
generic-only approval, omitted test evaluation and unauthorized executable change
all fail closed. Preserve accepted ordinary-test evidence semantics: historical
test failure accepted by a reviewer is distinct from the integration turn's own
required verification outcome.

No application change occurred in filing this record. No live provider, image
build/selection, Docker or Git mutation is authorized by this follow-up.


## 2026-09-07 — the bounded extension, pinned before implementation, claim114090

baton.claude. Plan item 1. Revalidated first: the three owned files are
byte-identical to the hashes `evidence/review-114048/audit.json` records —
`integration_contract.py` `03e346c2…`, `tools/integration_bundle.py`
`ee7a41f5…`, `tests/tools/test_integration_bundle.py` `645b16f5…` — and the
parent's delivered workload/entry/recipe/image bytes are unchanged too. Read:
this record, `PLAN.md`, the parent's `review-2026-09-07T22-48-26Z.md`, and
`evidence/review-114048/mode-scope-evidence.json`.

### What the public owners actually supply, established rather than assumed

**Existing-test authority HAS an owner.** `job_manager/documents._paths` says
it in the source: an accepted Job's `test_scope` is "the bounded test-change
authority a later reviewer and integrator check a proposal against", stored as
a repository-relative path set with duplicates and escapes already refused.
`_job_evidence` already binds it to `admission.resolved_account`'s
`scope_digest`, so a second reading of the Job store that drifted refuses. That
part of the account is sound; what is missing is not its owner.

**The independent review's own content HAS an owner, and the bundle carries
only a pointer to it.** `verdict_of` answers a verdict whose retained
`review_result` is the reviewer attempt's frozen output — `result_id`,
`manifest_digest` and one `artifact` per collected output, each with
`output_name`, `content_digest`, `bytes` and a `file://` `locator`. The digest
is `workspaces.directory_manifest`'s `tree_digest` over a DIRECTORY, and the
bytes are in manager custody. `review.json` copies the references and stops
there, which is exactly the review's finding: locators are not readable inside
`/input/source`.

**Executable and mode-change authority HAS NO OWNER, and that is the gap this
record reports rather than papers over.** `JOB_COLUMNS` is `job_id`,
`submission_id`, `ordinal`, `input_digest`, `policy_digest`, `test_scope`,
`terminal_policy`; `JOB_MEMBERS` adds only `stages`. There is no mode scope,
no executable scope and no per-path decision member anywhere in the accepted
Job, the submission document, the checkpoint evidence or the eligibility
account. `evidence/review-114048/mode-scope-evidence.json` is the measured
proof: a real accepted world's row takes `round-1.txt` from base mode `100644`
to candidate mode `100755`, and neither its `job` nor its `review` projection
says one word about that.

So this extension does NOT invent one. A candidate carrying a mode change or an
executable addition is REFUSED BY THE PRODUCER with that exact gap named, and
the refusal is the deliverable for that case. Widening `job_manager` to carry a
mode scope is generic-core work this follow-up is explicitly not authorized to
do; it is the named next capability if the deployment wants such candidates to
be publishable at all.

### The extension, exactly

**One new evidence projection, `authority.json`**, eighth in
`EVIDENCE_DOCUMENTS`, closed members
`("schema", "scope", "review", "paths")`:

- `schema` — `baton.integration-authority/1`, checked by equality.
- `scope` — the accepted Job's own answer, re-spelled from `_job_evidence`:
  `job_id`, `stage_id`, `work_id`, `scope_digest`, `test_scope`. It is the
  same account `job.json` carries and is repeated here so one document answers
  "what authorizes this row" without a reader joining two.
- `review` — `verdict_id`, `attachment_id`, `disposition`,
  `reviewer_participant`, `result_id`, `result_digest`, and `documents`: one
  entry per materialized reviewer output, `output_name`, `tree_digest`,
  `bytes`, `entry_count`, and `files` — `path`, `digest`, `bytes` per file,
  sorted bytewise by path exactly as `directory_manifest` sorts them.
- `paths` — one row per path row of the envelope that NEEDS authority, in the
  envelope's own sorted order: `path`, `operation`, `base_mode`,
  `candidate_mode`, `requires`, `authorized_by`. `requires` is a sorted subset
  of `("existing-test", "mode-change", "executable-addition")`. `authorized_by`
  is one entry per requirement, `{"requirement", "kind", "entry"}`, whose only
  admitted `kind` in this build is `job-test-scope` and whose `entry` is the
  exact `test_scope` member that names the path. A row whose table is not
  covered is not published.

**The reviewer's frozen bytes travel.** A new `review/` directory holds
`review/<output_name>/<relative path>` for every file of every artifact, and
those are the bytes `authority.json`'s `files` digests name.

**How a requirement is decided, and it is not a filename heuristic.**
`existing-test` is required when the row is an `edit` or a `delete` and the
path is inside the accepted `test_scope` — the scope IS the enumeration, so
membership decides both that authority is needed and that it is supplied, and a
changed path that no scope member covers needs no test authority because it is
not a scheduled test change. `mode-change` is required when both sides exist
and their modes differ. `executable-addition` is required when the candidate
side is `100755` and there is no base side. The parent's filename predicate is
its own to correct; nothing in this producer consults a filename.

Deleting or editing a path that IS a test but that the accepted scope does not
name is not made publishable by this rule: it carries no `existing-test`
requirement here, and the WORKER still refuses it, because the worker is where
"is this a test the review evaluated" is answered against the materialized
review content. That division is deliberate — the producer states what the
accepted records say, and it never decides the import.

**Custody is resolved through the deployment's own record, never from the
locator.** `workspaces.configured_workspace_storage(store).place` is the
frozen, cross-checked answer for where attempts are allocated; an artifact
whose `locator` is not `file://` plus a canonical absolute path INSIDE that
configured store refuses before anything is opened. The directory is then
walked with the module's existing no-follow discipline, measured with
`workspaces.directory_manifest`, and required to answer exactly the artifact's
`content_digest` as `tree_digest` and its `bytes` as `total_bytes`. A missing
directory, a link at any component, a digest that disagrees or a measurement
above the bound refuses with the exact gap; no fallback reads it another way.

### Bounds, and the one accepted number this changes

    MAX_REVIEW_FILES   32     files across all materialized reviewer outputs
    MAX_REVIEW_BYTES   1 MiB  total materialized reviewer bytes
    MAX_REVIEW_OUTPUTS 8      artifacts one frozen review may carry
    MAX_AUTHORITY_BYTES 1 MiB the projection's own ceiling (MAX_EVIDENCE_BYTES)

`FIXED_FILES` becomes `2 + 8` and the derived path bound becomes
`(MAX_BUNDLE_FILES - FIXED_FILES - MAX_REVIEW_FILES) // 2` = **235**, down from
the accepted 251. It is a REDUCTION and it is derived from the same
`contracts.canonical` 512-member manifest ceiling everything else here is
derived from: the publication manifest is one array with one entry per emitted
file, and review files are emitted files. The parent's FINDING pins 251 and
must adopt 235 when it consumes this; that is a consequence of this extension
and is named here rather than left for a reviewer to compute.

### The schema version moves, and both spellings move together

`BUNDLE_SCHEMA` becomes `baton.integration-input/2`. The envelope's member set
is closed and the evidence tuple is closed, so an eighth projection and a
`review` directory are not additions a `/1` reader may ignore — and this
campaign's rule is that the version is in the name so a reader from another
generation is refused by an equality test rather than left to find out. The
producer and the worker contract are both this Work's files and move in one
commit; the conformance case that holds their constants equal is what keeps
them one decision.

### What this deliberately does not do

It does not decide an import, does not evaluate reviewer prose, and does not
turn a generic approval receipt into permission. It authors no `approved`
boolean and no review document of its own. It does not touch
`integration_workload.py`, `integration_entry.py`,
`tests/manager/test_integration_worker.py`, the registry, or any generic core
module. The worker-side consumption of `authority.json` and the corrected mode
test belong to the parent, which owns them.


### Correction, same claim114090: the review travels INSIDE its projection

The extension above pinned a `review/` directory of materialized files. I built
it, measured what it did to the consumer, and it is the wrong shape. Recorded
here as a supersession rather than silently rebuilt, because the reasoning is
what makes the replacement obviously right:

**A directory per reviewer output makes the bundle three levels deep.** The
parent's `integration_workload.measure_bundle` bounds a bundle at
`MAX_BUNDLE_DEPTH = 1` — the root, then `evidence` and `blobs` — because that
is what a published bundle was. `review/<output_name>/<file>` is deeper, so
EVERY bundle became unmeasurable by the accepted consumer: 30 of the parent's
62 cases failed, all of them on "bundle-unreadable", none of them about
authority. An extension whose first effect is that the consumer cannot read any
bundle at all is not the smallest compatible one.

**And it spent the path bound for nothing.** Reserving 32 emitted files took
the accepted 251-path bound down to 235, which the parent's FINDING would then
have had to adopt — a second consequence bought with the first.

**So the reviewer's documents travel inside `authority.json`**, as
`files: [{path, digest, bytes, text}]` under each output. The layout does not
change at all: no new directory, no new depth, `FIXED_FILES` is `2 + 8` and
`MAX_PATHS` is `(512 - 10) // 2` = **251, the accepted number, unchanged**. The
bound that matters becomes the projection's own — `MAX_EVIDENCE_BYTES`, 1 MiB,
which already applied to every evidence document — with `MAX_REVIEW_FILES` (32)
and `MAX_REVIEW_BYTES` (1 MiB) bounding the account inside it.

**What this costs, stated rather than discovered later: the review's documents
must be UTF-8 text.** A canonical JSON document carries text, and the frozen
artifacts declare `application/octet-stream`. A reviewer output this producer
cannot decode REFUSES with that exact gap named — it is not base64-wrapped into
readability, because a reviewer's evaluation of a test change is prose, and a
binary review document is a case for an operator rather than for an encoding
layer here. Every file's `digest` is still taken over the ORIGINAL BYTES from
custody, so the account remains bound to what the frozen review measured
whatever this document renders.

The rest of the pin above stands unchanged: the locator check against the
configured workspace store, the one-pass no-follow copy as the measurement, the
authority account's shape and coverage rule, the closed requirement vocabulary,
and the refusal for mode changes and executable additions that no accepted
record supplies.

## 2026-09-07T23:16:55Z — independent review, claim114231

**Confirmed clarification:** documents._paths defines the accepted Job test_scope
as bounded test-change authority. It is the structured accepted scope owner.
This supersedes any reading of the original research that additionally requires
prose Work/plan bytes merely to replace that field. The requirement to inspect
the exact independent review's content and test-change evaluation still stands;
scope membership alone is not that evaluation.

**Confirmed acceptable boundary:** /2 with inline UTF-8 review text and251 paths
is a coherent extension. No current accepted record supplies executable/mode
authority; continue refusing those candidates. Optional support is recorded as
W114252 for a later executable-import capability pass, not added to this scope.

**Confirmed defects:** review-2026-09-07T23-16-55Z.md and
evidence/review-114231/probe.json show publication through a custody ancestor
symlink to outside configured storage, and reader acceptance of rewritten review
bytes under unchanged frozen identities, foreign scope identity and missing
materialized outputs. The public copied_manifest helper canonicalizes its root
before walking; it does not itself supply the claimed original-root no-follow
proof. The reader verifies inline self-checksums but not their binding to the
existing frozen review/Job projections.

**Current disposition:** changes required supersedes claim114090's ready-for-
acceptance state. Repair custody ingress and full internal authority correlation
within the existing three-file ownership. PLAN schedules the bounded fixture/
assertion corrections and added probes. Prose evaluation and actual import remain
parent-owned; no generic-core or parent file authority is added. Keep the single
provider outcome together for this correction, reassessing at handback.

**Evidence:** three candidate hashes match;18 tests added, no methods removed,
seven existing methods changed within scheduled fixture/evidence scope. Retained
175-test transcript contains exactly the two known parent incompatibilities;
101 child and12 image cases report passing. Earlier broad logs predate this
source change; no final source gate for these bytes was supplied. Correct first,
then perform/coordinate the required ready-candidate gate with a recorded question
and budget. No redundant suite or broad run occurred in review. PROGRESS and
implementation bytes remain untouched by the reviewer.


## 2026-09-07 — the two binding defects of review114231, corrected, claim114488

baton.claude. Revalidated first: the three owned files still carried the exact
bytes the review recorded. Both findings are real; both are corrected in the
same three files.

### Custody containment is now PHYSICAL, and the owner gap is recorded

The first version compared the locator's LEXICAL prefix with
`configured_workspace_storage().place` and then handed the pathname to
`workspaces.copied_manifest`. That helper's `_real` resolves the root with
`realpath` before its own descriptor-safe walk begins — so its careful
traversal of DESCENDANTS proved nothing about the root or its ancestors, and
the reviewer's `custody_ancestor_symlink_outside_store` published a bundle
whose review files came from outside configured storage entirely, with every
digest matching because the bytes were identical.

**The configured store and the custody directory are each walked from `/` one
component at a time with `O_NOFOLLOW`.** Only then does lexical containment
mean anything: a link-free path lexically inside a link-free root is inside it.
Every byte is then read through the descriptor that walk produced.

**AND THE COPY IS GONE.** The tree is measured and read in ONE
descriptor-bound pass, with the bytes kept as they are digested — so there is
no measure-then-reopen window at all, no scratch directory, and no second look.

**THE OWNER GAP, RECORDED BEFORE IT WAS WORKED AROUND:** no public capability
in this build measures or copies a tree through a HELD directory identity.
`directory_manifest` and `copied_manifest` both take a pathname and `realpath`
it. Editing them is generic-core work this Work is not authorized to do, so
this module walks and measures through its own descriptors — in
`directory_manifest`'s exact spelling, because the frozen review recorded its
`content_digest` with that owner — and
`test_the_measurement_equals_the_public_owners_on_a_link_free_tree` holds the
two equal on a tree with no links. If a later Work wants one implementation, the
bounded owner change is a descriptor-taking variant of those two helpers.

### The account is now bound to the projections it duplicates

`_authority` validated the account against ITSELF. The reviewer's three probes
each kept the real, unchanged `job.json`, `review.json` and eligibility beside
an account that contradicted them, and all three were accepted.

The reader now requires, all as internal bundle correlation and none of it as
interpretation of reviewer prose:

- **scope** — `job_id`, `stage_id`, `work_id` and `scope_digest` equal to
  `job.json`'s; `work_id` and `scope_digest` equal to the eligibility account's;
  the scope digest RECOMPUTED from its own paths; and the same scheduled paths
  as the Job projection.
- **review** — `verdict_id`, `attachment_id`, `disposition` and
  `reviewer_participant` equal to `review.json`'s, `result_id` and
  `result_digest` equal to the frozen result's.
- **documents** — the COMPLETE set the frozen review collected, by name, with
  each output's declared `tree_digest` and `bytes` equal to the frozen
  artifact's, and each tree identity RECOMPUTED from the file records in the
  canonical content-manifest spelling. A partial or empty materialization of a
  non-empty frozen review is refused.
- **rows** — each account row's `operation`, `base_mode` and `candidate_mode`
  equal to the envelope row it accompanies.

**Recomputing those identities needs the canonical form the frozen owners took
them in**, and a worker in a container cannot import
`baton_v12.contracts.canonical`. The restricted subset those documents use is
spelled in `integration_contract.py` and held equal to its owner by
conformance — the same mechanism, and the same recorded gap, as the rest of
this campaign's two-spelling boundaries.

### Two clarifications adopted from the review

The accepted Job's `test_scope` IS a valid structured scope owner; this Work
does not additionally require a prose decision record to replace it. And
prefix membership does not establish that an out-of-scope changed test is
ordinary source — evaluating an actual changed test against the materialized
review is the PARENT's consumption boundary, and an empty account grants
nothing there. The test whose name claimed a refusal it never performed is
renamed to report what the producer actually observes.

## 2026-09-08T00:20:14Z — independent corrected-candidate review114618

**Confirmed:** all three claim114488 hashes match. Descriptor-bound custody
reading corrects the original root/ancestor escape and measure/reopen gap; the
new reader rejects the direct foreign scope, missing materialization and row
misdescription cases. Retained conformance and race coverage support these
bounded corrections. Empty authority rows still grant no unscheduled-test import
permission; semantic evaluation remains the parent's responsibility.

**Confirmed remaining P1:** _authority_review compares the two declared copies
of result_digest but never recomputes the digest of review.json.review_result.
Rewriting inline review text and its file/tree checksums plus the corresponding
frozen artifact references, while preserving the ORIGINAL result identity,
is accepted. Removing both materialized documents and frozen artifacts is also
accepted under the old digest. Independent real-producer-derived probes retain
both mismatched computed digests and actual returned bytes in
evidence/review-114618/probe.json. Canonical review_cycles.verdict_of already
requires digest(review_result) equality; the worker reader must preserve it.
This supersedes claim114488's assertion that both P1s are completely corrected:
the custody finding is resolved, while the authority binding remains incomplete.

**Verification reconciliation:** focused195/18.246s has exactly four parent
reason mismatches (110 child and12 image tests have no reported failures).
Broad5025/268.662s has15 failures/1 error/21 skips, comprising the previous
11-failure/1-error identity set plus those same four parent cases. The dossier
and /tmp broad transcripts are byte-identical. Independent entry probes show
all four malformed evidence cases now refuse as bundle-unreadable and start
zero providers. Earlier refusal is acceptable; exact parent test expectations
need parent-owned correction, without weakening refusal/no-provider assertions.
Historical reds remain unwaived; no suite was rerun by the reviewer.

**Disposition:** changes required, within this Work's existing contract/test
boundary. Exact review: review-2026-09-08T00-20-14Z.md. PLAN schedules the digest
check, real-owner negative/control evidence and bounded placeholder-fixture
correction. No new split is needed for this single missing reader check. Parent
joined acceptance remains pending. Reviewer changed only evidence/FINDING/PLAN;
author-owned PROGRESS and source/test files remain untouched.

## 2026-09-08 — bounded tuner takeover

The interactive recovery sequence transfers this unclaimed remaining correction
to baton.tuner alongside the parent takeover, so dispatch resumption does not
feed either product job back into K's repeatedly stranded session. This
supersedes baton.impl as the executor of this bounded correction; existing file
ownership, scheduled digest/fixture scope and independent baton.codex review
remain unchanged. The parent requires its own claim and retains its paths.
Reuse applicable verification and target the missing digest check. This does not
authorize a general tuner role expansion or include the separate ACP root fix.

## 2026-09-08 — Claude restored under the foreground setting

Slawomir explicitly selected disabling managed Claude background tasks and
returning implementation to Claude. This supersedes the temporary tuner
allocation above. Restore baton.impl while dispatch is paused; the operational
setting and restart precede resumption. W114716 owns that deployment change.
The single digest/fixture correction, exact path ownership, targeted verification
and independent baton.codex review remain unchanged. No candidate acceptance or
whole-suite rerun is implied by the reassignment.

## 2026-09-08T00:52:51Z — independent sign-off, claim114869

**Confirmed:** contract74f53b03, producer c7a60dcc and tests af16d770 match
return114857 and are retained in evidence/review-114869/. The new whole-result
digest comparison precedes artifact use and matches the public owner. Existing
checks remain; both reported tampering shapes now have specific real-producer
regressions, and the positive/fixture use measured result identities. All110
prior test methods remain AST-identical, with three additions and only the
scheduled shared fixture changes. Parent hashes remain at review114828.

**Disposition:** review-2026-09-08T00-52-51Z.md signs off the bounded child
correction for owner acceptance, superseding review114618's changes-required
status. Reuse reported374-pass focused evidence and retained prior gates; no
reviewer suite rerun. Parent joined acceptance and every historical red remain
separate. No live/image/runtime capability is implied by evidence-reader sign-off.

**Attribution clarification:** the latest author entry labels itself claim114743,
but canonical114743 is reroute,114827 is the implementation claim and114857 its
return. Preserve the original entry and append correction in the next author
account; exact bytes and this review are bound independently of that heading.
