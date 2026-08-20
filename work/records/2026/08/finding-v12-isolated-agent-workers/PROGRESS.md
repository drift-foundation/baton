# Progress

Design record created 2026-08-18 from the confirmed v12 operational
discussion. No implementation agent has claimed this roadmap for
implementation and no v11 code change is authorized by it.

## 2026-08-20 — design review checkpoint (Work `W2`)

Claimed by `baton.claude` under the "Implementer design review checkpoint"
section of `FINDING.md`, which authorizes critique only.

**Nothing was implemented.** No prototype, dependency, schema, product-code or
v11 runtime change was made under this checkpoint. The only files this Work
wrote are this progress entry and the append-only review artifact.

Review artifact: `review-2026-08-20T11-37-13Z.md`.

Method: every pinned decision was re-read against the tree at `bafc74f` plus
the session's uncommitted W1568/W1578/W2571 changes — `transitions.py`,
`projection.py`, `cli.py` and `tools/acp-baton-bridge/src/*.mjs` — and each
finding is labelled Confirmed, Observed, Inferred or Open according to whether
it was measured in the tree.

Ten findings, no blocking objection to the direction. The five that should be
resolved in the record before implementation order is chosen:

1. the pinned "v11 cannot enforce claim-before-execution" text is now partly
   false — W2571 closed the protocol half today, and only the filesystem half
   remains;
2. "assignment generation" has no v11 primitive, and the nearest one
   (`episode_seq`) is explicitly minted BEFORE the claim and unchanged by it,
   so keying capabilities to it would be wrong;
3. "read-only worker" contradicts "the worker must claim", because `claim` is
   an authority mutation — the record uses one word for two write boundaries;
4. the integration flow never says who APPROVES a proposal, though it
   specifies everything either side of that step;
5. `AGENTS.md`'s absolute prohibition on mutating Git operations forbids
   exactly what a v12 worker does in its private clone, and needs an explicit
   dated supersession scoping it to the canonical checkout.

Five more carried as Open decisions: the dossier layer as unisolated shared
state, the one unmechanical rule in an otherwise machine-checkable conformance
suite, two conformance invariants stated more strongly than a suite can prove,
runtime-profile probation having no v11 routing mechanism, and unowned clock
authority for every deadline in the design.

Four positive revalidations are recorded too, because they mean the design
builds on primitives that already exist: the readiness envelope already
reports `claimed` per row, `action_key` is already authority-derived and
already re-read before a turn, the ACP bridge already fails closed on an
unexpected permission request, and `release_claim` is already an exact
compare-and-swap.

One ordering recommendation: a bounded end-to-end spike between PLAN items 1
and 2, whose only deliverable is the corrections to items 1-4.

One out-of-scope defect observed and filed rather than fixed:
`docs/BATON-WORK.md` teaches `waiting` as a scheduler phase when the
vocabulary is `queued`/`active`/`block`/`parked`. Lightweight Work `W2693`,
no dossier.

## 2026-08-20 — second design review checkpoint (Work `W2`)

Claimed by `baton.claude` under the "Second implementer design review
checkpoint" section of `FINDING.md`, which again authorizes critique only.

**Nothing was implemented.** No prototype, dependency, schema, product-code or
v11 runtime change was made under this checkpoint either. The only files this
Work wrote are this progress entry, PLAN item 0k's state, and the append-only
review artifact.

Review artifact: `review-2026-08-20T16-00-50Z.md`.

Method: the complete record re-read against the tree as it stands NOW, which is
the material difference from the first review — W2571, W2645, W2693, W2780,
W2597, W2938 and W3243 all landed in the working tree after these rulings were
pinned, and two of them changed authority facts the design depends on.

All ten first-review findings are resolved, and two of the answers are better
than the review that prompted them: the authority-mediation boundary (the
manager owns the authority channel entirely, so the sandboxed model never
crosses it) and `no-certified-runtime` as a visible scheduler gate rather than
a silent absence.

Seven new findings, no blocking objection. The two to settle before ordering,
both arising from protocol facts newer than the rulings:

A. one-slot claim capacity is now enforced in `transitions.claim_work`, so how
   many live assignment generations one PARTICIPANT may hold is no longer a v12
   design choice — it is one, and the record neither says so nor draws the
   consequence for per-participant parallelism;
B. there are now two overlapping "nobody claimed" mechanisms on two
   authoritative clocks — W2938's canonical participant pickup obligation
   (authority clock, accepted policy threshold, already presented in Teams)
   versus the manager's claim-acceptance deadline (monotonic clock, per
   attempt). They can disagree, and "overdue" already means something.

Three that are small to rule and expensive to discover during implementation:
`plan-rejected` can loop, because ending the claim returns the Work to the
actionable pool with nothing gating a re-offer of the same unrevised plan; plan
immutability leaves the leaf `PLAN.md` status marks unowned when the implementer
maintains them today; and an isolated worker cannot file a discovery finding at
all, which contradicts the role-neutral recursive discovery rule in
`AGENTS.md`. One minor: the compact `W2@g3` generation form is display-only and
must never be accepted as a Work selector.

On the bounded spike: it covers the happy path and the two hardest safety
properties well, but exercises none of plan rejection, the conflict stop, the
claim-acceptance deadline policy clause, or the four gates AS four — all of
them newly pinned and therefore least settled. Credentials, retention, cache
sharing, signing and proposal-store layout stay open after it, and ordering
should not assume otherwise.

## 2026-08-20 — final consistency review (Work `W2`)

Claimed by `baton.claude` at seq 3547 under the "Final implementer design
review checkpoint". Review only; **nothing was implemented** under this
checkpoint either. The only files written are this entry, PLAN item 0u's state,
and `review-2026-08-20T16-31-16Z.md`.

The wake that preceded this claim was superseded before it could be acted on:
the approver rerouted W2 back to `baton.feat` at seq 3544 to add the
remote-adapter requirement and reclaimed it, so the assignment was re-passed at
seq 3546 with the expanded scope. Nothing was done under the stale offer.

All seven second-review findings are resolved, and B is resolved better than
proposed — rather than ranking two clocks, the manager-issued single-use claim
token's expiry becomes the one claim-acceptance deadline, leaving the
authority's pickup obligation as the single operator-facing signal. Each of the
record's four claims about that obligation was checked against the shipped
implementation (`transitions.py:601-638`, `projection.py:2768-2792`) rather than
taken on its word; the design and the authority agree. `W2938` is now closed
`satisfying`, so the capacity invariant the record leans on is accepted rather
than pending review.

The remote-adapter requirement is pinned consistently across the finding, the
spike and PLAN 0v/6, and no surviving text still defers remote execution to
later production conformance.

Not a clean return: six residual items, none blocking, none contradicting a
pinned ruling.

1. The conformance suite's invariant list — the thing that defines compliance
   for every later runtime — does not require the remote-specific properties
   the remote section itself makes mandatory (transport loss is not proof of a
   stopped process, fencing before uncertain quiescence, reattachment only on
   positive proof). The spike exercises them once; the suite would certify an
   SSH worker without them. Settle first, because the spike's traces are meant
   to seed the suite.
2. No post-claim deadline scenario exercises the pinned policy digest, the
   clause-naming requirement, or the generation compare-and-swap — and the
   policy digest is a manifest field about to freeze. One cancellation-grace
   force-stop would cover it.
3. `FINDING.md:314` still says parallel child Work is safe "because each child
   owns a distinct claim, proposal, and dossier", unqualified, beside the
   capacity ruling's "only across those distinct participants".
4. Plan immutability needs the transition clause the Git-mutation ruling got:
   `AGENTS.md:47` currently requires the plan status marks that the v12 rule
   forbids, with no stated cutover between them.
5. `file-discovery` always commits child Work, while `AGENTS.md` permits an
   independent top-level record — one sentence either way.
6. `FINDING.md:623-627` reads as though one mechanism covered both pre-claim
   and post-claim expiry; under the token model the first is self-enforcing.

## 2026-08-20 — closure consistency review (Work `W2`)

Claimed by `baton.claude` at seq 3611 under the "Closure consistency review
checkpoint". Review only; **nothing was implemented**. The only files written
are this entry, PLAN item 0z's state, and `review-2026-08-20T16-53-53Z.md`.

All six residuals from `review-2026-08-20T16-31-16Z.md` are resolved:
the conformance invariant list and PLAN item 4 both gained transport-partition
fencing and proof-bound remote reattachment; the spike's cancellation scenario
now expires a post-claim cancellation-grace deadline and must name the policy
clause and digest and compare-and-swap the live generation; parallel child Work
is qualified by distinct configured participants everywhere it appears; plan
immutability carries the v11-convention-stands cutover clause the Git-mutation
ruling set the precedent for; and the conformance paragraph proves the pre-claim
and post-claim deadline classes separately.

Residual 5 was resolved by replacing the mechanism rather than patching it — a
trusted intake agent decides what a draft becomes — which is a better answer
than either option offered, because it also stops asking a sandboxed worker to
classify a discovery it cannot see the ledger for.

Supersession hygiene checked directly: "Isolated-worker discovery" is retitled
superseded with a leading note, "Assignment record output" carries a partial
note naming exactly what changed and what stands, PLAN 0r is marked superseded
by 0y rather than edited away, and no unmarked occurrence of automatic
worker-side filing remains anywhere in the record. The mount model does not
collide with the manifest mount policy, output credential validation, or the
remote-adapter section.

One residual, decision-ready: the superseded text explicitly guaranteed that a
filed discovery is not lost when its parent proposal is rejected, and the
replacement does not restate it. Intake is described at review time and for
accepted source Work; a cancelled assignment never reaches review, and its
drafts are quarantined with no stated path to a trusted reader. That matters
here because this record's motivating incident is exactly a mid-assignment
cancellation. One sentence either way: route sealed or quarantined output to
intake with its disposition as provenance, or state that cancellation and
rejection forfeit drafts by policy.

## 2026-08-20 — closure check, clean (Work `W2`)

Claimed by `baton.claude` at seq 3631 for the final yes/no closure check.
Review only; **nothing was implemented**. Files written: this entry, PLAN item
0ab's state, and `review-2026-08-20T16-58-40Z.md`.

**Clean return.** The sole residual is resolved: cancellation, forced stop,
plan rejection and proposal rejection no longer forfeit discovery drafts — the
manager seals or quarantines the output and routes its drafts to trusted intake
with the source Work, generation, terminal/proposal disposition and
cancellation reason as provenance, and each draft receives a deliberate
decision before retention or disposal. All four terminal paths are covered,
including the force-stop the W2938 incident actually took.

The rule also adds a clause I did not think to ask for: inspecting a
quarantined draft neither accepts the source proposal nor grants the draft
authority. That is what makes routing a fenced generation's output to a trusted
reader safe.

No competing live rule. Checked against post-decision retention, the
cancellation/stale-generation preservation clause, the deadline ruling's
preserve-or-quarantine step, plan rejection's quarantined source-clone
evidence, and the one sentence that could have competed — the `file-discovery`
non-loss sentence, which sits inside the partially-superseded section whose
note removes exactly its mechanism, leaving its principle in agreement with the
new rule. Generation fencing is untouched: a stale worker's late writes land in
its own assignment-keyed mount and reach intake as disposition-stamped drafts,
never as publication.

Observed, not raised as a finding: this pass has no checkpoint section in
`FINDING.md` — its authority is the pass comment and PLAN 0aa.

## State

Closure check complete and clean. `W2` returns to `baton.feat`. The roadmap
remains unimplemented and this record remains authorization for nothing.
