# W325035 — the finite matrix, completed and asserted

`matrix3.py`, one run from `v12/python`: **117 checks passed, 8 scenarios
observed, 1 failed exactly as it must, 0 unexpected, 2.261s.** Evidence bound
by `MANIFEST.json`. Source base `372281f4a473300efb474d5a6573954c15ade367`;
zero changes under `v12/`.

`matrix-325037/` and `matrix-325138/` are preserved unedited with
`SUPERSESSION.md` beside each. Two claims of mine are withdrawn here, both
named in place: that this fixture exposes no engine-absence seam, and that the
missing diagnostic-owner operation is a product gap.

## The harness fails for its own reason

Review 2026-10-18T18-17-05Z found that comparing `outcome == failed` against
`expected_failure` let a setup exception or a cleanup failure satisfy the
self-check. `main` now requires, for scenario 0, a `CheckFailed` whose label is
exactly the intentionally-false check, with no setup traceback and no cleanup
failure; anything else is counted unexpected and the run exits non-zero. The
first corrected run proved this the hard way — invoked from the wrong working
directory, every scenario failed in setup and the harness refused the run
rather than reporting the self-check satisfied.

## 1 — a committed start whose reply is lost, then a restart

The seam the review named. `composing()` calls
`stage_execution.operations_from` directly so the caller owns the engine;
`serving()` installs a new engine world on every call and could therefore never
model a restart over the same runtime.

The engine really starts the container, and the manager process is stopped
inside the `ps` that follows: `execution_runtime: start-requested`, **no
attached runtime**, one real container minted, stage still `claimed`. A fresh
composition over the same stores and the **same engine state** then:

* asked the engine (`ps`, `inspect`) rather than re-deriving,
* adopted the **exact** runtime the lost reply named, on the same attempt,
* with the assignment unchanged,
* started **no second container** and prepared **no duplicate attempt**,
* invented no start or preparation failure, published no candidate,
* and the stage is serving again at `waiting`.

My previous handoff said this vector could not be demonstrated here. Withdrawn.

## 2 — an unknown runtime is not a dead one

One engine, two answers, in the order that matters.

| injected | axis | identity | stage |
| --- | --- | --- | --- |
| `status 1`, prose naming no container | unchanged `running` | retained | `waiting` (gated) |
| the engine's own `No such container: runtime-single-1` | `destroyed` | retained, exact | `exceptional` |

Absence is attributed to the exact attempt and the exact runtime id; no
replacement container is started for the dead one; successors stay blocked; the
authoritative proposal inventory stays empty throughout.

## 3 — same-authority recovery retains exact ownership

Across the recomposition: the assignment is identical member by member
(participant and generation included), the committed assignment history is
**not extended** by the recovery, the Work's route and handler are unchanged,
and the runtime ownership record is byte-identical. A handle naming another
authority UUID is refused by the identity gate.

The property two live compositions actually have is asserted too: sweeping the
**old** composition after the restart starts no second container, prepares no
second attempt, agrees with the fresh one on the stage state, and leaves the
same single assignment.

The connection to W321688's accepted recovery set is proved rather than cited:
this instance's store answers `baton.v12.python.authority` and this
deployment's own UUID through `Authority.stored_identity` — the same supported
probe, and the same two members, that `dossier recovery-check` certifies.
What is **not** claimed: that the OS or SQLite prevents a second writer.
Positively accounting for a previous instance's runtimes remains an operator
act, as W321688's own check says.

## 4 — the correction lineage, through the public readers

`_prepared` is not a lineage proof. `writer_for_attempt`,
`review_for_attempt`, `checkpoint_of` and `line_of` answer from the attempt and
its generation, which do not move:

```
gen 1  implementation  writer-17f33e9b…  ──writes──▶ checkpoint-f808f219… (frozen, revision 1)
gen 2  review          review-06d28a3e… ──reviews──▶ checkpoint-f808f219…   state: ended
gen 3  implementation  writer-bd646428… ──based on─▶ checkpoint-f808f219…   state: active
```

All three are on the deployment's one line, which is bound to this Work; the
reviewer is not the implementer; the first writer is revoked and the
successor's is active; the first round's candidate still stands as the only
entry in the authoritative inventory; and the review stage is `blocked` rather
than completed.

## 5 — explicit diagnostic ownership EXISTS, and my gap claim is withdrawn

The review refused my inference from missing projection keys, and it was right.
Asked of the Authority's own surfaces after a provider turn exits 1:

* the stage is `exceptional`, the **authoritative** proposal inventory is empty
  (read from `proposals_of`, not inferred), successors blocked,
  `pending_endings` empty, the Work open with no handler and no outcome;
* the operator names a diagnostic handler for the Work's route and
  `baton.diagnostician` **claims it** — an eligible assignment naming that
  participant and `principal:baton.diagnostician`, with the Work actively held;
* an identical claim replays rather than taking a second one;
* labelling the failure is capability-bounded: refused without
  `manage-work-labels`, accepted after the grant, and the Work is then
  discoverable by label;
* the alternative path works too — a dedicated diagnostic Work on its own
  route, created attributably and claimed by its own diagnostic owner, while
  the failed Work stays with the first one. One principal still holds one
  claim, which is why that second owner exists.

What remains true is narrower than what I claimed: nothing routes an
exceptional stage automatically — an operator must notice it. That is the
selected owner policy, a deployment act, **not** a missing product operation.
No product defect is claimed from this scenario.

## 6, 7, 8 — the rest of the finite matrix, now asserted

**6. An empty turn cannot falsely complete.** A provider that exits 0 and
writes nothing settles `exceptional`, freezes no completed result, publishes no
candidate, leaves successors blocked and is not offered a second attempt.

**7. A stale episode and a wrong principal refuse, and nothing moves.** Both
driven against a live assignment. Each refusal is checked, and after each one
the Work's status/phase/route/handler/outcome are unchanged, the live
assignment is still the same one, and **no assignment event was written**. The
refusals name the staleness and both identities respectively.

**8. Cancellation, exclusivity and an honest ending.** A second live claim
through a second writable handle is refused (`Work is already claimed`) — so
the enforcement is the claim's compare-and-swap, not the file handle; a
read-only handle refuses every transition and touches nothing; the live
cancellation removes the handler and leaves the Work open with no outcome, and
appears in the assignment events.

And one property I had never looked at: **the runtime-quiescence gate survives
the cancellation**, so a re-claim is refused with `Work is blocked by
'runtime-quiescence:1'`. A matrix that had asserted "cancel, then claim again"
would have asserted the opposite of what this product does. The owner's
installed `disposition close --outcome non-satisfying` then closes it with the
operator's own rationale and no acceptance.

## Provenance, stated precisely

Nothing in this run mutates this repository's history, index or working tree.
My earlier blanket "no Git command" was imprecise: the imported
`ComposedOneJobCase.vcs` runs `git` against the fixture's own disposable source
tree to build its history, under `GIT_CONFIG_GLOBAL=/dev/null` inside a
temporary root. No product source changed, no test suite run, no build, no
container, no live model, no live credential, no deployment, no raw SQL, no
forged receipt.
