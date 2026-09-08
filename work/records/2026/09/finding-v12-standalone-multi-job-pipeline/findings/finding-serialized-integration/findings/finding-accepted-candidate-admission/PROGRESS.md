# Progress

Ledger Work W101491 created; prepared for tuner assignment behind K's shared
boundary.

## 2026-09-06 — baton.tuner

Claimed W101491 and revalidated the committed coordinator, Authority proposal
and receipt projections, W71918 integration-checkpoint/line/writer projections,
and frozen worker-control contract. The coordinator is ready to store a proved
account, but the accepted shared boundary does not produce or validate the
generic profile/approved-scope account needed to prove one: `scope_digest` and
`profile_account_digest` exist only at the coordinator's receiving seam and in
its fixture, and Authority approval binds neither. Implementing against raw
caller values would violate the negative acceptance cases.

Recorded the exact gap in FINDING.md, requested K's interface through Baton
message M101589, made no production/test/shared-interface change, and returned
the Work to `baton.impl` as the dossier requires when K's accepted boundary is
insufficient.

## 2026-09-06 — baton.tuner — admission implemented

Reclaimed W101491 after W101714 closed with independent sign-off and
revalidated the current fifteen-member account against its accepted producers.
Added the disjoint `baton_v12.integration.admission` leaf. Its
`admit_candidate` operation takes only coordinator identities plus proposal and
line selectors; it re-resolves every account member from W71918's accepted
checkpoint and writer assignment, the writer's frozen output, Authority's
proposal plus passed/accepted/approved receipts and current target, and the
unique Job implementation stage plus its persisted input, policy and test
scope. It calls `queue.enqueue` only after those surfaces agree, so a refusal
allocates neither a rank nor a coordinator journal act.

Added the disjoint `tests.integration.test_admission` suite. Fifteen cases
cover the exact producer-derived account, exact replay, shared target ordering
across Authorities, two-connection duplicate admission, missing or wrong
policy receipts, receipt/assignment/checkpoint/result cross-wiring, missing
custody acceptance, stale target revision, Job Authority/input/policy/Work and
scope mismatch, ambiguous scope ownership, and malformed scope. Every negative
case asserts the coordinator remains unchanged.

Verification:

- `PYTHONPATH=src:. python3 -m unittest tests.integration.test_admission
  tests.integration.test_coordinator tests.integration.test_runtime`: 302
  passed, one skipped.
- `git diff --check` on both new leaf paths: clean.
- The broad parallel runner correctly refused the new test module as
  unregistered. This Work explicitly forbids tuner edits to shared registries,
  so no workaround or registry byte was written; K must add
  `tests.integration.test_admission` to the parallel registry before the broad
  gate can run.

## 2026-09-06 — baton.claude (K) — the parallel registry entry, on request

**This entry is K's and not the tuner's.** `baton.tuner` owns this leaf and its
progress; `tools/parallel_test.py` is a shared registry the accepted scope
forbids it to change, so it asked for the entry through the obligation on
W101491 and I made exactly that one change. No admission, coordinator, runtime,
export, schema or test byte was touched.

**The entry is a safety claim, so I checked it rather than copying the
siblings'.** The registry FAILS CLOSED by design -- it refused
`tests.integration.test_admission` until it was listed, which is the tuner's
own recorded observation and is the mechanism working. What I verified before
listing it as parallel: every case owns one coordinator database under its own
temporary root; the Authority, Job store and manager it admits against are
in-process fakes rather than real stores; nothing reaches a daemon, image,
container, credential, network or shared name; and the one threaded case races
two connections to ITS OWN database file, opened and closed inside the case, to
prove a concurrent exact admission returns one entry and one rank. That
reasoning is written into the registry beside the entry rather than left here.

### Verification

    PYTHONPATH=src:. python3 -m unittest tests.integration.test_admission \
        tests.integration.test_coordinator tests.integration.test_runtime
    -> Ran 302 tests, OK (skipped=1)

    PYTHONPATH=src:. python3 tools/parallel_test.py
    -> 69 parallel modules -> 4024 tests in 573 shards
    -> parallel source: 6 failures, 0 errors, 4 skipped
    PYTHONPATH=src:. python3 tools/parallel_test.py --phase serial
    -> serial source: 16 shards, 235 tests, 4 failures, 13 skipped

4259 tests, 10 failures, byte-identical to the recorded baseline: five
`test_boundary_inventory` cases and one `tests.authority.test_catalog` case,
whose failing sets name `worker_manager` entries this package is not in, plus
the four Docker-engine residue cases. The admission module's cases ran in the
parallel phase and none of them is among the failures.

The whitespace gate is clean.

## 2026-09-06 — baton.tuner — registry revalidation and review handoff

Reclaimed W101491 after K resolved M102221. Inspected the registry diff and
confirmed the new admission entry is classified parallel from its actual
resource ownership; no admission, coordinator, runtime, schema, export or test
byte changed in K's handoff.

Independent tuner verification at the returned snapshot:

- `PYTHONPATH=src:. python3 -m unittest tests.integration.test_admission
  tests.integration.test_coordinator tests.integration.test_runtime`: 302
  passed, one skipped.
- `PYTHONPATH=src:. python3 tools/parallel_test.py --phase parallel`: the new
  module collected and both admission shards passed; overall 4,024 tests with
  the same six unrelated baseline failures (five Worker Manager boundary-
  inventory cases and one Authority catalog case), zero errors and four skips.
- `git diff --check`: clean for the shared working-tree snapshot.

Implementation and verification are complete. The leaf now awaits independent
review; no immutable proposal digest was supplied.

## 2026-09-06 — baton.tuner — review response and completion

Independent review `review-2026-09-06T14-16-33Z.md` signed off with no
findings. It checked the production Authority, Job Manager and Worker Manager
return shapes against the members the admission leaf consumes, confirmed the
15-member producer-derived account and pre-enqueue refusal boundary, and
accepted K's separately attributable registry entry.

After reclaiming the signed-off Work, reran
`tests.integration.test_admission`, `tests.integration.test_coordinator` and
`tests.integration.test_runtime`: 302 passed, one skipped. The implementation
episode is complete and ready to unblock W101492. No immutable proposal digest
was supplied.
