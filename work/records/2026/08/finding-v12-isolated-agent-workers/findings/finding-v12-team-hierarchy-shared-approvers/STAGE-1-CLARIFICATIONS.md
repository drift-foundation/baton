# Stage 1 clarification addendum — K D1–D5

This addendum constrains CONSOLIDATED-PLAN.md revision 2 (SHA256 76aa436a578c3d488c878ff22e0f33c2c0acda462fb95534128f0a1286a947d0), preserving those reviewed bytes. It answers review-2026-11-22T04-17-25Z.md. It is a planning clarification pending narrow independent delta check, not implementation or live-execution authorization.

## D1 — exact trigger and new successor contract

For Stage 1-A, use the retained terminal verification-failed outcome: provider exited 0, required verification exited 1, runtime destroyed, reservation released. No provider process remains to resume. Retain original task, malformed verification argv, candidate identity and failure evidence unchanged.

Section 4, Stage 1-C and U5 must read “linked successor verification/review admission” wherever they suggest resuming that ended implementation. This is a NEW manager-owned admission contract, following REC-7 ownership principles but NOT today's fresh-attempt operation. Today's fresh-attempt retains the original specification and would repeat implementation; it does not supply this outcome.

The successor has its own execution identity linked to the failed attempt, exact retained candidate and immutable owner decision. It runs only owner-authorized corrected verification followed, on success, by independent review. It must never dispatch implementation as a side effect. The owner decision must explicitly authorize both the exact verification-input change and this successor's verification/review scope. A generic approval, “retry”, or reading an item is insufficient. Any phase-plan change is explicitly covered by owner approval, not inferred from a separate recovery approval. Cancellation, cessation/fencing, retained-byte integrity, ownership and finite-limit checks remain mandatory; original deadlines are not reset. Successor limits and admission semantics are reviewed contract details to pin before dependent implementation.

Acceptance includes no implementation dispatch, wrong actor/candidate/input refusal, changed-operation replay refusal, restart/duplicate notification producing at most one successor effect, exact original evidence preserved, and failed verification staying unaccepted. Stage 1-B must present the actual proposed verifier change and execution scope so the owner's decision is concrete.

## D2 — general exceptional analysis remains owned

Add a Stage 2 required outcome: extend automatic analysis beyond Stage 1's verification-failed ending to the selected exceptional endings of typed phases. Maintain a classification matrix for provider failures, deadlines/timeouts, review outcomes and unknown cessation. Which outcomes are exceptional versus ordinary correction paths is an OPEN owner-facing classification question; these examples are not blanket exceptional classifications. Each selected exceptional ending must automatically deliver attributable evidence to analysis, present options to the owner, and obey the conservative recovery gate. No recursive unlimited analysis of analysis failures.

Umbrella completion requires this outcome or an explicit owner disposition; Stage 1's narrow trigger does not satisfy the general requirement. Existing U2/U5 scope covers analysis-role binding and finite analysis-failure behavior; later classifications are not prerequisites invented for the first verification-failure loop.

## D3 — deterministic proof claims

The initial joined deterministic proof uses a scripted diagnosis. It proves automatic dispatch, exact evidence delivery, option presentation, owner gating and successor/review behavior. It does NOT prove a live model's diagnostic quality. No live-provider diagnostic-quality run is selected by this amendment.

## D4 — selected redirect examples

These follow the confirmed per-source project > team > global precedence and transitive substitutions:

- Project A -> B and global B -> C: that project's A-assigned queued/new work resolves to C.
- Cancel global B -> C while keeping project A -> B: the same work resolves to B.
- Team A -> B and global A -> C, with no project override: that team's A-assigned work resolves to B; other work follows its own applicable rules.

Healthy running agents remain in their original execution. U6 keeps genuinely unsettled interactions, including overlapping deferrals and a destination lacking the selected model, rather than re-asking these settled chain cases.

## D5 — deferral acceptance and implementation ownership

After an owner-selected deferral, unrelated eligible work proceeds and work dependent on the deferred result waits. Pool-control 4-B acceptance includes restart during a deferral, duplicate due-time triggers, at-most-once authorized resumption, and a renewed failure returning to the owner rather than automatically retrying again.

W385331 currently owns clarification/discovery/continuation; it has NOT been assigned exceptional analysis or recovery merely by similarity. Replace Stage 1's assumed W385331 ownership with “implementation Work allocation pending explicit coordinator recording before execution.” Before implementation, create/allocate bounded 1-A/1-B/1-C Work and canonical dependencies as authorized, or explicitly allocate an accepted scope extension in the existing owning record and ledger. W9901 remains the umbrella, and W385331 is an integration interface whose existing scope is preserved. This addendum itself changes no claim, graph edge or implementation scope allocation.

## Next gate

K delta-checks D1/D2 and the D3–D5 corrections only. No repeat full-plan review is needed. After that, select the bounded Stage 1 contract/analysis binding and establish implementation ownership before coding. Existing later-stage open decisions do not block the first useful loop unless a concrete dependency is demonstrated.
