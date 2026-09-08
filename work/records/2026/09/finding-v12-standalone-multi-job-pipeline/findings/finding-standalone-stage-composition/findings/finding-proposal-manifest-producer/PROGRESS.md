# Progress

## 2026-09-06 — baton.claude — checkpoint 1: revalidation run, two blockers reported

Claimed W103874 and ran PLAN item 2 against the current tree before touching
any authorized path. State: **changes requested / returning for targeted
review**, per the frozen-path section's own instruction.

What the checkpoint asked for is half delivered and half impossible, and the
split is clean:

**The manager/Authority half is pinned in FINDING and needs nothing further.**
Every one of those manifest members has an exact accepted source reachable from
`attempt_id` through accepted reads only — no mutable `/output` path, no
custody bytes. `runtime_profile_digest` comes from the retained
`inputManifest`, which is the one manifest a production caller does retain, so
that load succeeds.

**The worker-owned half cannot be built in the five authorized paths, for two
independent reasons.**

1. No worker-authored fact survives into any document the producer may read.
   The worker CAN emit a namespaced `result_metadata` claim today and
   `baton_worker` does carry it into `/output/output.json` verbatim. The
   manager then validates that envelope, keeps its digest, and drops the
   document — `_envelope` is bound and never used — while
   `sealing._answered` writes a literal `"result_metadata": {}` into the
   sealed `artifactOutput` from the manager's own declaration. The
   `completionManifest` is never retained, so its digest names a document
   `load_manifest` cannot return. `evidence` and `extensions` are manager
   literals too, and the framed answer's `recap` is validated and then
   discarded — the word appears nowhere else under `baton_v12/`. So the
   adoption step the boundary describes has nothing to adopt from.

2. There is no proposal head. The worker clones and detaches at the declared
   base, copies that checkout to `/output/candidate` **without `.git`**, and
   publishes a content tree plus a unified diff. It never commits, and no
   commit-producing or object-naming vector exists in `claude_agent.py` or
   `source_profiles`. `proposal_head` is a `gitObject` that
   `driver._publish_operands` hands the Authority as `candidate_digest`, so
   there is no honest value for it in this build.

I did not bridge either one. Both fixes for (1) are in `worker_manager`, which
this Work's frozen paths exclude, and the change is not cosmetic: a sealed
`artifactOutput`'s opaque member is manager-authored today, and every
downstream reader of a sealed result is entitled to that. Both workarounds for
(2) — inventing a head, or minting a commit in the workspace clone — are
forbidden by name in the approved-ownership section, and the second would
publish an object name that exists only inside a container the manager then
destroys.

One further point that review should settle in the same round, recorded as
Proposed in FINDING: `manifestHeader.created_at` cannot be the wall clock. The
required regression is that exact replay returns the SAME retained digest, and
retention is keyed by the digest of the bytes, so a clock instant retains a
second account of the same frozen result on every replay. The only frozen
instant the producer has is the result manifest's `manager_observed_at`.

Not done, deliberately: no namespaced subdocument is pinned. Pinning a contract
whose carrier is unreadable and one of whose three facts does not exist would
be a ruling made to unblock a handoff rather than because it is right.

Files: only this dossier's `FINDING.md`, `PLAN.md` and `PROGRESS.md` were
written. `v12/worker/claude_agent.py`,
`v12/python/tests/manager/test_claude_agent.py`,
`v12/python/src/baton_v12/integration/driver.py`,
`v12/python/src/baton_v12/integration/__init__.py` and
`v12/python/tests/integration/test_driver.py` are byte-identical to the
inspected baseline. No test was run, because nothing was changed to test.

## 2026-09-07 — baton.claude — the producer, built against both accepted providers

Reclaimed W103874 once both providers landed. Revalidated their bytes first:
`worker_manager/sealing.py`, `worker/claude_agent.py` and
`source_profiles/checkout.py` all match their signed-off digests exactly, and
the two incompatibilities I reported on 2026-09-06 are genuinely gone rather
than worked around. State: **awaiting independent review.**

Changed three of the five authorized paths:

- `integration/driver.py` — `retain_proposal`, the claim adoption, the object
  name rule, and two extractions.
- `integration/__init__.py` — the export.
- `tests/integration/test_driver.py` — additive producer cases.

`worker/claude_agent.py` and `tests/manager/test_claude_agent.py` are in this
Work's original five-path list but are now the accepted provider's, and both
are byte-identical to its signed-off record. I did not touch them.

What the producer does is read every member back from its accepted owner and
adopt exactly four facts from the worker. The half I pinned on 2026-09-06
survived contact with the tree unchanged, which was the point of pinning it
before the providers existed.

Two rules were EXTRACTED rather than restated. `_publish_signature` and
`_expected_answer` are now one spelling shared by the producer and the
publisher; the alternative was a producer whose signature its own consumer
recomputes differently, which is a Work that cannot publish at all and would
have looked like a manifest bug. `_one_output` is the selection half of
`_one_proposal_output`, split because the producer has nothing to cross-bind
against yet. Both refactors are behaviour-preserving and the eighteen accepted
publication cases still pass unchanged.

The `created_at` point I raised as Proposed is now load-bearing rather than
theoretical: it is the frozen result's `manager_observed_at`, and one of the
new cases exists specifically to fail if somebody makes it a clock read.

Verification. The producer cases retain for real: a real `ControlStore`, a
really retained `inputManifest` and `resultManifest`, a really retained
`proposalManifest`, a real `load_manifest` load-back, and then a real
`publish_candidate` over that digest with only the Authority supplied. The
required regressions are covered — positive with real retention and load-back,
exact replay returning one retained account, missing/wrong-namespace/extra/
short claim data, malformed and cross-namespace object names, a transport the
manager never measured, wrong assignment, zero/two/absent/non-proposal
outputs, target drift retaining nothing and publishing nothing, and no secret
or raw output byte in the retained document.

Suites: `tests/integration` 399, `tests/job_manager` 387, and the worker,
source-boundary, checkpoint, output, sealing, text-sweep, secrets and
dependencies suites 448 — all passing. The four object-name cases needed hex
with letters in it, because an all-digit name cannot tell an upper-case
spelling from its own.

## 2026-09-07 — baton.claude — the derived manifest identity, corrected

Reclaimed after `review-2026-09-07T02-59-03Z.md`. The probe reproduced before I
changed anything: `evidence/review-producer-boundaries.py`, three tests, one
erroring at `retain_manifest` with `'manifest_id' breaks maxLength`.

**The defect, and why it is worth stating as a rule.** A result id and a
manifest id are both `opaqueId`, bounded at 160 characters. I composed the
manifest id as `proposal-<result_id>`, which is longer than its own type allows
for every result id from 152 characters up — so the producer refused perfectly
valid frozen results, and refused them at retention rather than anywhere a
reader would look. A prefix is a composition whose length is its INPUT'S; a
bounded member can only carry an identity whose length is this module's own.
The digest-based `_identity` helper already in this file is exactly that, and it
was sitting one function away.

The manifest id is now `_identity("proposal-manifest", account)` over the same
account `proposal_id` is taken from — one dictionary rather than two spellings
of it, since the property both identities carry is that two frozen results never
share a name and one frozen result always produces the same one. Nothing is
truncated: truncation is precisely how two distinct results become one name.

Regressions added at the boundary the review named: result ids at 151, 152, 159
and 160 characters all stay proposable with both derived identities inside the
ceiling, and four distinct maximum-width result ids produce four distinct
identity pairs. The one existing manifest-id assertion changed to the derived
form, which is the exact expectation the fix requires and no more.

**A correction to my own handoff.** I described the producer cases as supplying
"only the Authority". That was wrong: they also mock `frozen_output_of` and
`assignment_of`, which are attempt-row reads a store cannot answer without a
whole lifecycle. Retention, load-back and publication are real; those two reads
are not, and the reviewer's probe is what covers them.

Verification. The reviewer's probe re-runs unchanged: three tests, exit 0.
`tests/integration` is 401 tests and `tests/job_manager` 387, both passing; the
worker, sealing, output, text-sweep and secrets suites are 347 more, passing.
The scoped whitespace check exits 0. Provider bytes are untouched and still
match their accepted records.

Candidate digests: `integration/driver.py`
`d7a3e63e2b9ef8b6fffc6eb219790a3df7fd58c3be2ffeb59727bf9284dfd8b1`;
`integration/__init__.py` unchanged at
`c2c749ce5d2c1ecadb5d8b0e1ae5ea2943a650779af88ca04dcc9b0b41f97dbd`;
`tests/integration/test_driver.py`
`253c22ced28342012af4a05c942599ef26122ec3d224e2763eb69a344cd7d4a6`.
