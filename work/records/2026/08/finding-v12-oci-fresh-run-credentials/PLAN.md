# Plan

1. Revalidate the W6634 credential spike against current assignment, manager, adapter, and live-secret contracts.
2. Pin the trusted profile-provider seam, volatile-root ownership, permission model, and fixed mount contract.
3. Implement live registration, secure materialization, read-only mounting, failure cleanup, positive-absence proof, and forgetting.
4. Add focused positive, negative, leak, permission, failure-injection, and real-OCI regressions.
5. Run focused and full v12 verification, then request independent review.

## 2026-08-27 — implementation

- [done] 1. W6634's credential spike revalidated BY MEASUREMENT rather than by
  reading: every rule the finding names was removed and the suites re-run.
  Seven of nineteen were unestablished, including both permission rules the
  acceptance states outright.
- [done] 2. The seams are as the finding pins them; nothing needed moving. The
  trusted profile provider, the assignment-private volatile root, the fixed
  read-only mount and the registry ordering are all where they belong.
- [done] 3. No behaviour changed. The code already implemented every rule; what
  it lacked was anything holding it to them.
- [done] 4. Positive, negative, leak, permission and failure-injection
  regressions, plus a real-engine suite that asks the DAEMON what it recorded,
  and a 19-mutation measurement over all five suites.
- [done] 5. Focused and full v12 verification run; returned for independent
  review.

### For review

- [judgement] The behaviour is unchanged on purpose. A decision to rewrite as
  well as establish is a different Work than this finding describes.
- [stated, not hidden] `O_EXCL` on the credential file is unreachable through
  `materialize` — the root check and `exist_ok=False` guarantee an empty root.
  Kept as defence, and said so rather than left looking like coverage.

## 2026-08-27 — independent review changes requested

- [required] Treat `_discard(root) == False` during failed materialization as
  unresolved cleanup: keep all materialized bearers registered and surface a
  credential-lifetime refusal rather than propagating an ending that forgot
  them.
- [required] Apply the live-secret guard before the duplicate-candidate engine
  call, including the candidate `runtime_attempt_id`; add a regression proving
  no preflight argv receives a live bearer and a mutation that removes that
  earlier guard.
- [required] Replace the real-engine teardown case's direct
  `CredentialHome.tear_down` call with evidence that respects the confirmed
  provider boundary. Positive runtime absence/removal belongs at the adapter
  or W6636 crossing, not in a test that deletes the mount source first.
- [evidence] Append corrected gate evidence: W26296 is now the explicit owner
  of the `check_input_pair` inventory failure, so the current claim that it has
  no owner is stale.
- [test hygiene] Make the new engine suite remove and assert absence of its
  `v12-w26284-engine-*` temporary roots; `_release` currently changes modes
  but never deletes the directories it creates.

## 2026-08-28 — review corrections applied

- [done] The [P1] unprovable cleanup. The failed-materialization handler now
  branches on `_discard`'s answer: a proved removal forgets and re-raises the
  original failure; an unproved one keeps every bearer REGISTERED and raises
  its own `policy/credential-lifetime` ending. A registry disarmed over bytes
  still on disk is a §13 scan that cannot fail, which is worse than no scan.
- [done] The [P1] pre-sweep leak. The §13 argv walk moved from `run_vector` —
  which swept only the vector it composed — to `EnginePort.__call__`, which is
  what every vector passes through. `start`'s duplicate probe now refuses
  before the engine is reached at all, and the reviewer's own reproduction
  reports `0 calls containing bearer` against `2` before.
- [done] The [P1 test gap]. The engine suite stays inside fresh-run delivery
  and failure, which is the resolution this finding's own boundary chooses
  between the review's two. The teardown case no longer starts a container it
  cannot prove absent, and a new case covers the one runtime-absence question
  this provider owns: a start the engine refused settles through the adapter's
  real listing before the delivery is released.
- [done] Regressions. `test_a_removal_that_cannot_be_proved_keeps_every_bearer_live`
  drives `_discard`'s false answer;
  `test_the_duplicate_probe_cannot_carry_a_bearer_to_the_engine` uses the
  CANDIDATE attempt label rather than `participant`, which is why the case that
  existed could not see the leak.
- [done] Mutations. Three changes: the two failed-materialization anchors moved
  with the correction, a third makes the absence proof vacuous the way ignoring
  the boolean did, and the argv mutation removes the sweep at its single owner.
  The credential-mount anchor was re-pointed through the word "credential"
  because W26291 added a byte-identical launch mount. **20 of 20 caught.**
- [done] Test hygiene. `test_credentials_engine._release` removes its tree and
  asserts absence; measured before and after a fresh run at 347, delta 0.
- [done] Evidence. `evidence/w26284-2026-08-27-credential-provider.txt` is KEPT
  as produced; `evidence/w26284-2026-08-28-review-corrections.txt` carries the
  baseline correction (W26296 owns `check_input_pair`, the registration landed,
  the accepted baseline is SIX), why nineteen caught mutations were not
  sufficient, the scope decision, and the 347 pre-existing temporary trees.
- [done] Gates re-run: focused 265, `test_credentials` 80, real-engine 7,
  parallel 1553 with the accepted six, serial 105/0.

## 2026-08-28 — independent review sign-off

- [signed-off] The failed-materialization absence proof and the engine-port
  argv sweep were independently reproduced on the corrected tree.
- [signed-off] The real-engine tests now respect this finding's fresh-run
  boundary; the post-runtime lifecycle crossing remains W6636's.
- [verified] Focused reviewer suite: 267 green. Targeted diff check: clean.
- [limitation] The managed reviewer process could not access the Docker socket,
  so the seven real-engine cases and 20/20 mutation run remain
  implementer-produced gate evidence. See
  `review-2026-08-28T07-43-36Z.md`.
