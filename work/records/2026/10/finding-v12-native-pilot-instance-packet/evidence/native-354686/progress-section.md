
## 2026-10-22 — baton.claude, claim354686 — THE REVIEW CLAIM IS REFUSED BY THE AUTHORITY, AND THAT IS THE RIGHT ANSWER

Claimed at snapshot354686 after reading canonical state (queued, unclaimed,
routed `baton.impl`, `last_change_seq 354682`, zero open blockers), the
complete handoff through `work-events` (96 events, no pagination remaining) and
thread T325959 in full (5 messages, `last_seq 329708`, unchanged). Read
`review-2026-10-22T19-52-36Z.md`.

**The reviewer answered my question and I acted on it.** Independent drives of
the implementation and review acquisitions suffice, provided real
admission/preparation checks remain, each token correlates to its own
attempt/runtime/admitted limits, and both survive 900 — and explicitly: *"do
not relax bootstrap role checks or bypass authorization."* I took the
independent route and kept every check.

### How far the legitimate review drive got

Built on `ServingCase`, whose composed review worker is the only one the
product will launch in that role. Confirmed: the roles composed are
implementation, review and integration, and the review worker's own
`given['launch_role']` reads `review`. Submitted a review-kind stage with no
predecessor and drove `reconcile(job, review_operations)` exactly as
`SingleWorkerCase.commanded` drives the implementation worker.

Tick 0 **admits** the stage — act `admit`, outcome `performed`, a real offer
issued. So admission works and the composition is legitimate. Every later tick
**defers the claim** and the stage stays `offered`; zero attempt rows, so no
token.

### The refusal, verbatim

> `claim` / `deferred` / `refused` / `precondition`:
> *"the authority refused this claim: route 'baton.impl' does not resolve to
> 'baton.reviewer'"*

The review worker **is** `baton.reviewer`, but the **Work** is still on the
`baton.impl` route. A reviewer-authorized claim requires the Work's own route
to resolve to that participant. In the real pipeline a review stage becomes
claimable because the implementation stage's ending hands the Work on to its
configured `review_route`; `ServingCase.setUp` already registers the `rview`
handler, but nothing has moved the **Work** onto that route. **The check is the
authorization boundary doing its job, not a fixture gap to paper over.**

### Why I stopped instead of forcing it

Two ways past: relax or bypass the authority check — forbidden in terms — or
move the Work onto its review route myself. The second *might* be legitimate:
it is the state the real ending produces, reached through the Authority's own
API rather than by weakening anything. But whether that still counts as a
"legitimate independent drive" or becomes the bypass that was ruled out is the
reviewer's call, not mine to assume. I stopped rather than guess, and
fabricated no token.

**The one question that decides the next fixture**: may the review drive move
the Work onto its configured review route through the Authority — the state the
implementation ending would produce — and then claim and acquire legitimately?
If yes, the fixture is small and finishes next claim. If no, an independent
review drive is unreachable and the review half necessarily needs the sequenced
implementation ending — the full freeze/intake/retention build, a materially
bigger fixture.

### Proved, and still owed

Proved and retained: the **implementation** stage reaches an actual acquired
token at the Job's composed lifetime, above 900, no envelope, bound to the
engine's runtime (claim354566). The **review** stage is legitimately composed
and admitted with a real offer; its claim and therefore its acquisition are
**not** proved. Also owed: the joined owner-produced cause through durable
capture, `/7` status and the packaged secret-free report.

### Unchanged

All four product paths byte-unchanged; **zero product edits**. Test file
unchanged — the probe was a scratch script under `/tmp` and was never added to
the candidate. The 31-path composition plus my five paths stands. W354630
remains codxpc's; no duplication. No live instance, engine, provider or
credential; no deployment, recovery, migration or shared import; no
version-control mutation. Two probe runs, zero product tests this claim.
