# Owner requires the token-baton design — 2026-09-26

Slawomir reaffirms the previously stated design: an expiring exclusive token
grants permission to perform the resource operation; another thread cannot
acquire conflicting ownership until the outstanding baton is returned safely.
Owner directs: "we need token-baton design in there". This is the required
implementation direction for W270664, not an optional proposal or permission
to resume descriptor-inference experiments.

## Required contract

- Acquire exclusive, durable resource ownership atomically in a short database
  transaction. The record binds the governed resource/conflict domain, operation,
  owner/execution identity, token generation and expiry. Eligibility, completed
  replay and token acquisition are one atomic decision, not separated by a gap.
- Commit before external I/O. Filesystem, engine, network and application calls
  into other stores must not run while holding the database lock. Database/library
  internal I/O remains the exception. Pure database-only transactions need no
  separate token merely for existing; the token governs work continuing outside
  the short transaction.
- All conflicting allocation, adoption/use and removal entries consult the same
  authoritative token state. No second thread or process may acquire a conflicting
  token while the first is outstanding. Bind aliases/overlapping resources to the
  conflict domain; unrelated resources may progress independently.
- Completion and return are short conditional transactions naming the exact
  token/generation. Stale owners cannot complete, release or clear another owner's
  token. Durable outcome/replay must not authorize a repeated external effect.
- Expiry begins revocation; it is NOT automatic permission for replacement use.
  Stop/fence the old executor and every helper/writer able to affect the resource,
  and positively establish cessation before replacement admission. Unknown prior
  effects remain held. Safe settled interruption/retry remains required.
- Token checks alone cannot stop an already running filesystem writer. Retain
  actual exclusion/cessation enforcement. In-process guards, manager identity or
  inferred file-descriptor provenance are not substitutes for durable ownership.
- Use an explicit usable connection to the governing authority. The recently
  accepted no-implicit-reopen refusal is compatible infrastructure, not the baton
  design itself. Do not reopen that resolved detour.

## Delivery and ownership

Current claimant Claude retains W270664. Before more affected implementation,
read this ruling, append it to FINDING.md and update the current PLAN checkpoint,
using the supported contract revision if applicable. Explicitly supersede any
contrary implementation direction; preserve historical decisions and evidence.
Map existing reservations/claims to the contract above. Reuse those that satisfy
it; record and implement the minimum missing token lifecycle for the selected F2
paths. Do not merely rename a flag or declare unsupported guarantees.

The prior prohibition on a broad second lease system remains a scope constraint,
not a reason to omit the required token. A concrete minimal schema/API extension
needed by this contract must be recorded with exact paths and compatibility
effects; no unrelated architecture or deployment migration is selected. Report
a genuinely wider migration requirement precisely instead of guessing.

First deliver one executable vertical slice: token acquisition, controlled
external operation, completion/return and competing-caller refusal on the actual
removal/allocation boundary. Focused real disposable-store proofs must include
thread/process contention, no external I/O under DB lock, unrelated progress,
expiry with still-live effects held, positive cessation before reacquisition,
stale return/completion, interruption and safe retry/replay. Then finish the
remaining selected F2 entry paths and obligations. Independent review evaluates
the token contract directly. No broad plan-only loop or other audit fixes.

No claim takeover or overlapping product edits. Existing W257624 acceptance,
source checkpoints and historical probes remain preserved. No live provider,
engine/deployed recovery, cleanup or Git mutation is authorized by this ruling.
Prompt owns this decision note only; claimant and reviewer retain their existing
source, test, progress and review ownership. Acceptance still returns to owner.

## Later owner clarification — Docker termination is the enforcement mechanism

Slawomir clarifies: "active token is tied to an active Docker image, if token
expires, active Docker is shut down so it can be safely reset that was the design".
Operationally the running object is the Docker container/instance; the image is
its immutable launch input. Bind the token to the exact running container identity
and execution generation, retaining image provenance as appropriate.

The required sequence is: acquire exclusive token, bind the controlled Docker
execution before permitting its resource effects, execute with no DB lock held,
and return the token on completed execution. On expiry, record revocation and
prevent replacement admission, stop the exact token-bound container, positively
confirm it has terminated and cannot continue resource effects, then permit
reset and a new token generation. Stop/confirmation/reset I/O occurs outside DB
transactions. Docker stop uncertainty or surviving associated writable helpers
keeps the resource held; expiry or issuing a stop request alone is not cessation.

This specifies the concrete enforcement mechanism behind the preceding abstract
cessation wording and supersedes any interpretation that a generic process token,
in-process mutex, database handle, or holder's voluntary check alone implements
the owner's design. Map existing runtime/container accounting to the token; name
any manager-owned effects outside that fence and place them under enforceable
ownership rather than silently treating container termination as proof about
unrelated writers. Do not assume a container ID exists at initial reservation:
preserve reserve-before-launch and uncertain/delayed-launch exclusion while
binding the eventual container to that exact token.

Use the real selected coordination/runtime boundaries with controlled Docker
adapter evidence for focused deterministic verification. This decision selects
the product behavior, not a live Docker run or deployed reset. Pin this latest
clarification alongside the earlier ruling before affected implementation/review.

## Later owner sequencing — return the next review for specification alignment

Slawomir selects baton.prompt to consolidate the normative v12 DESIGN.md, then
Claude to review and sign it off. The next review of W270664 MUST return the
Work to owner custody at baton.decide for realignment with that specification,
with current candidate, evidence and exact remaining gaps preserved. This
explicitly supersedes the routine direct-to-implementation continuation for that
next review only. Do not claim full acceptance merely to return it, silently
continue another correction loop, or release someone else's live claim. The
current reviewer records the outcome and passes through the normal claim protocol.
No competing edits to W270664 product or review files are selected.
