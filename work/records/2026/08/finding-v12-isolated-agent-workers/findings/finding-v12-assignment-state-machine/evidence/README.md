# Executable model evidence

Run from this directory:

```text
python3 -m unittest -v test_assignment_state_model.py
```

Verified 2026-08-22 against checkpoint `c529b28`: **61 tests passed** for
`SPEC.md` version `1-ruled`. The `0-design` package ran 13; the first
`1-ruled` package ran 27; focused review round 1 added seven cases and the
response four; round 2 added four and the response three; round 3 added two
and the response four; round 4 added one and the response two; the W4487
decline ruling added seven.

The scenarios cover expired, replayed and settlement-timed-out tokens; offer
uniqueness scoped per Work over one shared control store; one-live-claim
capacity checked at offer issue and at claim; a competing claim; manager
restart before and after claim; one runtime per assignment with exact
reattach; cancellation that fences the generation, ends the assignment, frees
the participant's claim slot and installs a typed `runtime-quiescence` gate;
uncertain versus destroyed quiescence and the pinned certified-isolation
clause; sealed cancellation output, trusted intake, and policy-controlled
discard; per-Work contract progression, its first minted generation and its
`contract-runtime` gate; an immediate same-participant successor rejecting the
old generation; atomic plan-revision gating; result freeze and proposal
binding; the four immutable, replay-only verification/review/approval/
integration receipts; target movement; every ruled terminal-close case; and
the separation of Work phase from attempt state.

They also cover the effectively-once boundary the focused review opened: a
settlement timeout that resolves its fixed claim operation before expiring an
offer (and leaves an unanswerable lookup accepted), manager-owned mutations
that are effectively-once in the control store too, runtime observations that
never regress from a terminal `destroyed`, immutable frozen output, a refused
integration that journals one attempt and replays its refusal, and replay
signatures that bind the durable reason, rationale, or outcome prose.

Round 2 of that review added the settlement boundary proper: a fixed claim
operation becomes durably committed or retired in one authority act before any
control row calls it terminal, a refused claim is terminal for its operation,
and intake and cleanup carry the operation identities the transition table
promises.

Round 3 closed the settlement contract: the claim-settlement deadline is its
own durable boundary rather than the token's, retirement requires reaching it
while reconciling an already committed claim does not, and every settlement
compares the FIXED claim operands so an operation-id collision fails closed
instead of binding another participant's assignment to this offer.

Round 4 closed the last restart boundary: a retirement binds the terminal
disposition it caused, so a manager crashing between the authority record and
the control row cannot let whichever entry path notices next relabel a
settlement timeout as a refused claim, or the reverse.

W4487 (2026-08-22) added the decline path the contract had never modelled at
all. W151 §7 required a declining worker to echo the claim bearer; the frozen
worker-control schema requires `claim_token: null`; the approver kept the
non-secret envelope and superseded W151's requirement. The seven scenarios
pin every property the bearer requirement was carrying — the exact binding
that cannot terminate another offer, effectively-once with the reason in the
signature, verifier consumption so the token is dead afterwards, no claim and
no capacity taken, restart durability, and the freeing of the Work for a fresh
offer — plus the half it would have been easy to lose, that ACCEPTANCE still
requires the exact unspent bearer.

The model is design evidence only. It imports no Baton or `v12/` application
module and changes no runtime behavior.
