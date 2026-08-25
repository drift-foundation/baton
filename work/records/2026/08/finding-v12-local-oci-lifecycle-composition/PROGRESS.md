# Implementer progress — local OCI lifecycle composition

Created 2026-08-24 by `baton.claude` on claiming W6636, as the record requires.

## The nine dependency edges are installed

The handoff asked the route handler to add them before implementation. All nine
are in, each with its rationale recorded on the edge:

**W5 components** — W6631, W6632, W6633, W6634.
**Manager contracts** — W6592, W6627, W6628, W6629, W6630.

## Not implemented, because the brief's own precondition is unmet

The assignment opens with it: *"After all component and manager prerequisites
close satisfying, compose the approved sequential consent/execution OCI
topology."*

Measured on the current tree rather than assumed — **none of the nine has
closed, and none has a satisfying outcome**:

| Work | status | phase |
|---|---|---|
| W6631 materialize sources | open | queued |
| W6632 adapter core | open | queued |
| W6633 worker image | open | active |
| W6634 sealed output/credentials | open | **block** |
| W6592 manager composition | open | queued |
| W6627 agent-session/runtime | open | queued |
| W6628 output receiver | open | queued |
| W6629 intake/retention/cleanup | open | queued |
| W6630 section 13 security | open | queued |

Four of these I implemented myself in this session and returned for review;
they are in review precisely because nobody has yet confirmed they are right.
Composing on top of them now would build an integration on nine unreviewed
foundations, and the integration's own tests would then encode whatever those
components got wrong — which is the failure that makes an integration review
worthless rather than merely early.

W6634 is a stronger case still: it is itself **blocked**, on contracts that do
not exist. There is nothing there to compose.

## What this Job would need that does not exist yet

Its deliverables name them directly: consent teardown and exact activation need
W6627's agent-session and runtime protocols; **effectively-once**
start/inspect/cancel/**freeze/collect**/destroy needs W6628's output receiver
and W6634's collector; positive absence needs W6632's adapter, which is written
but unreviewed; and the destroy/retain path needs W6629 and W6630.

The mutable Docker restart/race/failure evidence the brief asks for is the one
part I could run today — Docker 29.1.3 is reachable on this host. Running it
against components that may change would produce evidence about a system that
will not exist by the time this Job is reviewed, which is worse than no
evidence because it looks like coverage.

## Recommendation, not a decision

Let the nine settle. This Job is an integration and it is correctly last.

If the intent was for me to begin a *scaffold* — the composition's shape, with
its component seams named and left unimplemented — that is a coherent thing to
ask for and a different Job from the one written here; I would want it stated
before building it, because a scaffold that ages against nine moving components
is the same waste in a smaller package.

## State

**Edges installed, no implementation.** Parked in `block` behind its nine
prerequisites, which is where an integration Job with nothing to integrate
belongs.
