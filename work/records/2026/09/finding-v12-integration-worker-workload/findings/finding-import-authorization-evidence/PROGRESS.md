# Progress

No implementation yet. Created by baton.codex for the separately scoped evidence
provider discovered in review114048; the executing author appends progress here.

## 2026-09-07 — baton.claude — claim114090, the authority evidence extension

Delivered: `authority.json`, the eighth evidence projection, carrying what the
accepted records actually say about every reviewed row that needs saying-about,
with the independent review's own documents materialized out of manager custody
so a runtime can read them.

### Revalidated before acting

The three owned files matched the hashes `../../evidence/review-114048/
audit.json` records — `integration_contract.py` `03e346c2…`,
`tools/integration_bundle.py` `ee7a41f5…`, `tests/tools/test_integration_bundle.py`
`645b16f5…` — and the parent's delivered bytes were unchanged. The design was
pinned in FINDING before any edit, as PLAN item 1 requires, and one correction
to that pin is appended there with the measurement that forced it.

### What the owners could and could not supply

**Existing-test authority has an owner and it is the accepted Job's
`test_scope`** — `job_manager/documents._paths` calls it "the bounded
test-change authority a later reviewer and integrator check a proposal
against". The account names the exact scope entry that covers each changed
path, bound to the same `scope_digest` admission resolved.

**The review's own content has an owner and the bundle carried only a pointer
to it.** The verdict's retained `review_result` names each collected reviewer
output by tree digest and a `file://` locator into manager custody. The
producer now resolves those through `configured_workspace_storage` — the
deployment's own cross-checked record, not the locator string — copies each
tree with `workspaces.copied_manifest` (one no-follow pass, which is the owner
W26283 wrote precisely so that measuring and copying cannot disagree), requires
the measured tree digest to be the one the frozen review recorded, and carries
the files inside `authority.json`.

**Executable and mode-change authority has NO owner in this build, and that is
reported rather than invented.** `JOB_COLUMNS` carries `test_scope` and nothing
else per-path; no accepted record anywhere names a file mode. So a candidate
carrying a mode change or an executable addition is REFUSED BY THE PRODUCER
with that exact gap named, and the reader refuses one that claims such a grant
anyway. Widening `job_manager` to carry mode scope is generic-core work this
follow-up is not authorized to do and is the named next capability.

### The correction I made to my own pin, and why

I first built the reviewer's documents as a `review/` directory of emitted
files, then measured what it did to the consumer: the bundle became three
levels deep, the parent's `measure_bundle` bounds it at one, and **30 of the
parent's 62 cases failed on "bundle-unreadable" — none of them about
authority**. It also took the accepted 251-path bound down to 235. An extension
whose first effect is that the accepted consumer cannot read any bundle is not
the smallest compatible one, so the documents travel inside their own
projection instead: no new directory, no new depth, `FIXED_FILES` 9 → 10, and
**`MAX_PATHS` stays at the accepted 251**. The cost is that a reviewer document
must be UTF-8 text; one that is not refuses with that gap named rather than
being encoded into unreadability. Both the original pin and this supersession
are in FINDING.

### Verification

`tests.tools.test_integration_bundle` — **101 passing, 0 failures**, up from
83. The 18 new cases run against the REAL accepted world: the reviewer's frozen
bytes travel and equal the custody bytes; the scheduled scope travels with its
binding; a row needing nothing is absent from the account; a scheduled
existing-test change is granted by the Job entry that covers it; a mode change
and an executable addition each refuse with the provider gap and publish
nothing; a locator outside the configured store refuses; an absent and a
drifted custody tree each refuse; and on the reader side, an account that does
not describe its own table, a grant of a kind this build does not admit, a
grant naming a scope entry that does not cover its path, a mode-change row, a
review rendering that is not the content its digest names, and a `/1` bundle
are all refused. The bounded fixture edits PLAN item 2 schedules are the
`authority` document the read-back fixture now publishes, the two owner answers
added to the projection stub, and the derived-bound assertions.

**TWO PARENT CASES NOW FAIL, both of them cases review114048 already ruled
must change, and neither is mine to edit.** Reported here rather than left for
the next runner to find:

- `test_an_edit_preserves_the_reviewed_mode_and_an_executable_one[100755]`
  errors because the producer now refuses to publish a 0644 → 0755 candidate.
  That is the review's own P1: "candidate mode is not permission", and its
  scheduled correction is to distinguish preserving 0755, an explicitly
  authorized mode change, and an unauthorized change that starts no provider.
- `test_the_same_change_inside_the_scheduled_scope_is_admitted` fails because
  the parent's `derived()` helper copies the authority account unchanged while
  replacing the path table, so the account no longer describes its own table.
  The parent's correction owns worker-side consumption of this account.

Everything else in the parent's 62-case suite and all 12 image cases still
pass, which is the measurement that says this extension did not break the
consumer generally. No broad source gate was re-run for this candidate: the
review asks not to rerun the broad suite merely to complete a handoff, and the
delta from the retained runs is exactly the two cases named above plus the 18
added here.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_contract.py` | `e4d5b2ef5b610cfb348bbb37ca3437f7f7c25a4ce6828dfd62864871b9cbf813` |
| `v12/python/tools/integration_bundle.py` | `7279f3140d2f2968b7b3b2e4b45f054e1956606d8fd418abb01d89a17464e4ae` |
| `v12/python/tests/tools/test_integration_bundle.py` | `20fea94a5ca463197952c7228003621254262a4daaa26d60390f4d2618303468` |

No parent source, parent test, registry or generic-core file was edited. No
live provider, image build or selection, container, or version-control
mutation of any kind occurred.

## 2026-09-07 — baton.claude — claim114488, the two binding defects corrected

Both P1s of `review-2026-09-07T23-16-55Z.md` were real. Both are corrected in
the same three owned files, each with the probes the review named.

### Revalidated before acting

The three owned files still carried the exact bytes
`evidence/review-114231/audit.json` records.

### P1 — custody traversal followed an ancestor symlink out of the store

**The defect was mine and the review's probe is exact.** I compared the
locator's lexical prefix with the configured store and then handed the pathname
to `workspaces.copied_manifest`, whose `_real` calls `realpath` before its own
descriptor-safe walk. That walk protects DESCENDANTS; the root and its
ancestors were never proved, so a link inside storage pointing at identical
bytes outside it was followed and published.

**Corrected:** the configured store and the custody directory are each walked
from `/` one component at a time with `O_NOFOLLOW`, and every byte is read
through the descriptor that walk produced. The copy is gone entirely — the tree
is measured and read in ONE descriptor-bound pass, so there is no
measure-then-reopen window, no scratch directory and no second look.

**The owner gap is recorded rather than worked around:** no public capability
measures or copies through a held directory identity, and editing
`directory_manifest`/`copied_manifest` is generic-core work this Work is not
authorized to do. So this module measures through its own descriptors, in that
owner's exact spelling, and
`test_the_measurement_equals_the_public_owners_on_a_link_free_tree` holds the
two equal.

Probes added: a symlinked ancestor inside the store pointing outside it (the
reviewer's own case), a symlinked custody root, a link inside the custody tree,
and a **transient swap at the actual read boundary** — the proved directory is
moved aside and replaced by a link to other content after the descriptor is
open, and the read returns the original files and never the planted one.

### P1 — materialized authority was not bound to its owner

`_authority` validated the account against itself, so a rewritten review with
the original frozen identity, a foreign scope identity, and an entirely absent
materialization were each accepted beside the real, unchanged projections.

**Corrected:** the reader now binds scope identities to `job.json` and the
eligibility account and RECOMPUTES the scope digest; binds review identities to
`review.json` and its frozen result; requires the COMPLETE materialized output
set by name with each declared tree digest equal to the frozen artifact's and
**recomputed from the file records**; refuses partial or empty materialization
of a non-empty frozen review; and compares each account row's operation and
both modes with the envelope row it accompanies.

Recomputing those identities needs the canonical form the frozen owners used,
which a container cannot import, so the restricted subset is spelled in the
contract and held equal to its owner by conformance — the same mechanism and
the same recorded gap as this campaign's other two-spelling boundaries.

All three reviewer probes are now regressions, plus a row-misdescription case
over three internally valid but different values with every owner identity left
intact.

### The two wording corrections the review asked for

`test_an_existing_test_change_outside_the_scheduled_scope_refuses` is renamed
to `test_a_change_outside_the_scheduled_scope_carries_no_grant` and its
docstring now reports what the producer actually observes — it publishes with
an empty account — and says that evaluating an out-of-scope changed test
against the materialized review is the parent's consumption boundary. The
overflow case's docstring said 235 after the inline-evidence supersession
restored 251; it says 251.

### Verification

`tests.tools.test_integration_bundle` — **110 passing**, up from 101 and from
the accepted 83. `tests.manager.test_integration_image` — 12 passing.

**FOUR PARENT CASES NOW FAIL, and the change is a reason rather than a
behaviour.** The contract's new correlation refuses these derived bundles
EARLIER, during `read_bundle`, so the workload reports `bundle-unreadable` with
a precise observation instead of its own later word:

- `test_a_review_that_did_not_accept_refuses`
- `test_a_scheduled_test_change_with_no_review_document_refuses`
- `test_an_authority_account_about_another_job_refuses`
- `test_evidence_about_another_checkpoint_refuses`

Each still publishes `refused` and still starts no provider — the outcome
assertion passes and only the reason assertion fails. This is strictly earlier
fail-closed behaviour; updating those four expected reasons is the parent's
correction, in files this Work must not edit.

### The required gate

QUESTION: does anything outside the four suites that exercise these bytes
depend on the changed producer or contract? COMMAND:
`PYTHONPATH=src python3 -m unittest discover -s tests -t .` from `v12/python`.
BUDGET: one run, about five minutes, which is what the three retained broad
logs took.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_contract.py` | `2f8b42eb4f82949e97c2ef660d6fa5d39384eaeb6d5688f3bb90be715175fcf2` |
| `v12/python/tools/integration_bundle.py` | `c7a60dcc1fc1df989153c3368aeac4677950e42c1473088c65af998f43f63058` |
| `v12/python/tests/tools/test_integration_bundle.py` | `e2f175173bed6bec4887f982d2f54b9fa29b7b7b375192db0539cc030587ac31` |

No parent source, parent test, registry or generic-core file was edited. No
live provider, image build or selection, container, or version-control mutation
of any kind occurred.

### The required gate, run and reconciled

QUESTION: does anything outside the suites that exercise these bytes depend on
the changed producer or contract? COMMAND: `PYTHONPATH=src python3 -m unittest
discover -s tests -t .` from `v12/python`. BUDGET: one run, about five minutes.

**ANSWER: nothing does.** `evidence/implementation-114488/source-gate.txt` —
**5025 tests in 268.662s, 15 failures, 1 error, 21 skipped**. Reconciled
against the three broad logs `evidence/review-114048/` retains (4985/11F1E,
4987/11F1E and 4987/12F1E):

- the campaign's eleven historical failures are unchanged and unwaived — six
  boundary-inventory, four live-engine cleanup, one authority-catalog — as is
  the one registry error;
- the four ADDED failures are exactly the four parent cases named above, and
  nothing else moved;
- the count rose by 38, which is the cases added to this Work's own module and
  the parent's.

`test_dogfood_retry_engine`'s extra failure from the third retained log does
not appear in this run. I am not claiming that means anything about it: W114077
holds that observation for its own diagnosis and it remains unwaived.

The four parent failures are a REASON change and not a behaviour change: each
still publishes `refused` and still starts no provider, and only the expected
reason string moved because the contract now refuses earlier. Correcting those
four expectations belongs to W110935, whose files this Work must not edit.

## 2026-09-08 — baton.claude — claim114743, the frozen-result digest binding

The one P1 of `review-2026-09-08T00-20-14Z.md` was real, and both of its
probes are now regressions. `integration_bundle.py` is unchanged: this is one
missing measurement in the reader and the fixture that could not have caught it.

### The defect, in one sentence

`_authority_review` compared the account's `result_digest` with `review.json`'s
`review_result_digest` and then trusted the artifacts that digest names —
but **both copies of that identity travel inside the bundle**, so rewriting a
reviewer's collected output together with its matching artifact row, or
emptying the outputs on both sides, kept an identity that no longer measured
the result it named. The reader returned invented text as the review's own
words in the first case and zero files from a non-empty frozen review in the
second.

**Corrected:** `integration_contract.py:906-917` recomputes
`canonical_digest(review_result)` and holds it equal to
`review_result_digest` BEFORE any artifact is used, keeping every existing
per-file, tree, complete-output-set and identity comparison. This is the
comparison the real owner already takes over the same document in
`worker_manager/review_cycles.py` `checkpoint_verdict`, which is why the
reader can take it without inventing a rule.

### Why the positive fixture could not have noticed

`ReadBackCase.review_account` declared the literal `sha256:555…` — an identity
that measures nothing — so every positive read-back agreed with a digest that
was never a digest of anything. The scheduled fixture change replaces it with
the ACTUAL digest of the result the fixture retains, taken with the frozen
owner's own `baton_v12.contracts.digest`, composed once by a new
`frozen_result` helper that both the account and `review.json` are derived
from. Each negative case's intended mismatch is preserved: the missing
materialization case still refuses on the complete set, the rewritten-review
case still refuses on the tree identity it declares, and the foreign-scope case
still refuses on the Job.

### The regressions, and the proof they catch it

Three cases in `TheAuthorityAccountComesFromRealOwners`, all built from REAL
producer output and read by the real worker reader, copying the published
bundle file by file rather than making read-only custody writable:

- `test_the_retained_result_measures_to_the_digest_it_declares` — the
  real-owner positive: an untouched bundle reads back, its retained result
  measures to its declared identity, and `contract.canonical_digest` answers
  what `baton_v12.contracts.digest` does over that same document, so the two
  negatives are about tampering and not about two spellings of one digest;
- `test_a_rewritten_output_under_the_original_identity_refuses` — the
  reviewer's `rewritten_output`, asserting afterwards that
  `review_result_digest` really was preserved and that the actual digest now
  differs;
- `test_the_outputs_removed_under_the_original_identity_refuse` — the
  reviewer's `removed_outputs`, with the same preserved-identity assertion.

**FALSIFIED, not assumed:** with the new comparison removed from the reader
and nothing else changed, the two negatives fail with `BundleRefusal not
raised` — the reviewer's two false acceptances — and the positive still
passes. The reader was then restored and verified byte-identical by SHA-256
before the gate below.

### The verification this claim ran

QUESTION: does the corrected reader still admit real accepted evidence, refuse
both tampering shapes, and leave the parent's consumption unmoved? COMMAND:
from `v12/python`, `PYTHONPATH=src python3 -m unittest
tests.tools.test_integration_bundle tests.manager.test_integration_worker
tests.manager.test_integration_image tests.manager.test_claude_agent`. BUDGET:
one focused run, under a minute.

**ANSWER: 374 tests in 29.604s, OK.** `test_integration_bundle` is 113, up
from 110; `test_integration_worker` is 77 and unchanged; image 12; claude_agent
172. **No broad rerun.** Every module in this tree that imports
`integration_contract` or `integration_bundle` is one of the four above
(`grep -rln` over `v12/python` and `v12/worker` names only those three test
modules, `parallel_test.py`'s registry, and the worker's own entry/workload),
so the four modules ARE the dependent set for this change, and the previous
claim's 5025-test gate already answered the wider question for the bytes this
one adds a refusal to.

| Path | SHA-256 |
| --- | --- |
| `v12/worker/integration_contract.py` | `74f53b031f392a615141c1d2be6552989658b6f5b15b82cc9f16294a3ee5be92` |
| `v12/python/tools/integration_bundle.py` | `c7a60dcc1fc1df989153c3368aeac4677950e42c1473088c65af998f43f63058` |
| `v12/python/tests/tools/test_integration_bundle.py` | `af16d77052b94aa85c707966f673ac1b1cbb26eec013b709be76f704e391bd38` |

### Correcting the previous entry's closing claim

The claim114488 account above ends "no container … of any kind occurred" while
the gate it reports is the whole 5025-test suite, which contains real engine
tests that DO start containers. That statement was wrong about that run and is
corrected here rather than rewritten there: the deterministic child proof —
this module's 113 cases and the 374-test focused run — starts no container, no
live provider, no credential and no version-control mutation, while the broad
5025-test transcript it reconciled against is an ordinary full-suite run whose
engine cases behave as they always do. The eleven historical failures, the one
registry error and W114077/W114516 remain unwaived, and no current engine state
is inferred from those logs.

### What this claim did not touch

No parent path, no generic-core file, no image, no live provider and no Git
operation of any kind. The parent's four reason expectations needed no further
adaptation: `test_integration_worker` is green at 77 against these exact bytes,
which W110935's own handoff (claim114742) already recorded from the other side.
