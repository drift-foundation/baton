# The bounded instruction artifact — W321780

This is the `instructions` member of the **`baton.dogfood-task/2`** launch task
the packet describes. Review 2026-10-18T09-16-00Z asked for it to be completed
rather than promised at selection time, so it is written here and pinned in
`PINS-321780.json`.

**`/2`, not `/3`, and review 2026-10-18T09-38-00Z is why.** Both selected
holders check `baton.dogfood-task/2` by closed equality —
`claude_agent.py:117`, `dogfood_operator.py:768` — so a `/3` launch task asking
for `/3` to be implemented would refuse at both ends before this turn could
begin. `/3` is what this turn **produces**; `CONTEXT-CONTRACTS.md` is its
acceptance surface and test data, not its envelope.

`<BASE>` and `<RUN>` are deferred: a base taken before W321528 is accepted would
bind an unaccepted candidate, and a run identity is the owner's to allocate.

**This document bounds the work by OUTCOME.** Per the standing AGENTS ruling of
2026-09-28, an implementation is judged by what it achieves, not held to an
exclusive list of files it may touch. What follows names the outcome, the known
traps, and where to coordinate — and leaves the means to the turn.

## What the turn is asked to build

Add the declared verification context and the versioned paired result contracts
to the two holders, so that a verification view is **declared** rather than
re-derived by hand at each holder.

The acceptance surface is `CONTEXT-CONTRACTS.md` in this dossier. It is the
contract, not a summary of one: the `/3` task shape, the `candidate` identity
document, the two preflight stages with their closed refusal tables, and the
three fresh result schemas with their five legal outcome combinations.

## The two holders

| holder | file | what changes |
| --- | --- | --- |
| worker | `v12/worker/claude_agent.py` | accept `baton.dogfood-task/3`, run Stage A before any provider work, build the declared view, run Stage B before the command starts, and publish `baton.dogfood-proposal/3` with its `baton.dogfood-context/1` member |
| operator | `v12/python/tools/dogfood_operator.py` | build its **own** fresh view from the retained output and publish `baton.dogfood-operator-evidence/1` from what it measured |

Both views are **new** work: `_verify` currently runs in the candidate itself,
so the worker needs a disposable view of its own just as much as the operator
does. Trap 6 below is the requirement, not an optimisation to weigh.

Helper and test changes beside these are expected — a contract this size does
not land without them. Two places need **coordination rather than avoidance**,
because changing them changes somebody else's answer:

- `src/baton_v12/source_profiles/checkout.py` owns the profile vocabulary, the
  base grammar and the profile/base pairing. Both holders should keep **asking**
  it rather than restating its rules; `dogfood_operator.py:744-750` is the
  delegation pattern to follow. If `/3` genuinely needs that package to answer
  something new, change it there once and keep both holders asking — do not
  grow a second copy of its rules in a holder.
- `tests/manager/input_roots.py` fixes where the 102 gate reads its fixture, and
  `PACKET.md`'s layout is built around that resolution. Changing it changes what
  the gate measures, so if the layout turns out to need it, say so in the result
  rather than adjusting the gate quietly to fit the view.

## Seven things that are easy to get wrong, named in advance

1. **`/2` stays frozen.** A new member on `baton.dogfood-task/2` is what DESIGN
   VER-1 forbids. A `/3` context arriving under `/2` must **refuse**, not be
   ignored; a `/3` task with the context absent must refuse too.
2. **The base is provenance, not the view's content.** Do not check
   `declared_base` out into the verification view, and do not require a finished
   candidate to equal it. The relationship is **ancestry** —
   `claude_agent.py:2452-2521` already proves exactly that and explains why
   equality would reject the second correction round.
3. **Verification runs over the provider-modified worktree, before the
   commit** — so a sealed task cannot name the resulting candidate, and must not
   try. What a turn measures after the provider belongs in its **published
   result**: the bounded, status-reported `changed_paths` and `removed`, with
   the exclusion `collection` disclosed. Do **not** add a whole-tree rehash:
   `_line_status:2759` records owner ruling 2026-09-21T12:47:17Z retiring that
   guarantee by name, and the honest scope is "a path status cannot see is
   neither measured nor delivered".
4. **A context fault supplies no verdict.** A missing required path, a
   digest-mismatched input and a failed materialization are `refused` with
   `command: not-run`. If the implementation deleted a path the task requires,
   that is a Stage-B `missing-input`, never a test failure.
5. **Nothing unsafe becomes durable.** No child output, no credential, no
   absolute host path and no exception prose in any published record. The
   `detail` member of a context outcome is a bounded structural fact: which
   declared member or input name failed.
6. **NEITHER VIEW IS THE EDITED CANDIDATE, and this is the requirement the
   whole Work descends from.** `_verify` today runs "in the candidate copy",
   which for a line is the retained worktree. VER-3 requires a **fresh private
   view at each holder**: a command that wrote or deleted a source path would
   otherwise alter the retained candidate, and a timeout cleanup that removed
   that "view" would remove the candidate. Both the worker's disposable view
   and the operator's are **new bounded materializer work**. Each holder
   deletes only its own view; the candidate and the sealed inputs are
   byte-unchanged on success, test failure, timeout, failed start and partial
   materialization alike.
7. **The operator's view needs BYTES, and the transport is INCREMENTAL.**
   `objects.bundle` is created for `base..HEAD` (`claude_agent.py:3016-3018`)
   and carries no base history, so the view must first be seeded from the
   accepted-base object source — the deployment's own retained repository,
   whose `refs/heads/main` only `tools/accepted_base.py` advances — and must
   **refuse** a missing prerequisite, an unsatisfied bundle, or a transport
   resolving some other head. No fallback to an ambient host checkout, and a
   digest does not supply a missing object. For a generic candidate the
   retained output *is* the tree. `PACKET.md`'s trace has the stage detail.

## Standing boundaries

Not an exclusive file list — these are the standing rules of the deployment:

- No Git mutation. Slawomir alone owns the index, commits, branches and history.
- VER-3's two named prohibitions hold: no generic recursive copier and no
  maintenance container. The two bounded view materializers in `PACKET.md`
  stages 6 and 8 are neither; each is declared as new work with its scope
  stated, and each exists to satisfy VER-3's own isolation requirement rather
  than to work around it.
- No whole-suite expansion. The focused obligations are in `VERIFICATION.md`.
- W321528's packet is somebody else's claim, and the `claude_agent.py` overlap
  with it is coordinated in W321776 rather than resolved unilaterally here.

## How the turn is judged

The 102-test credential gate passes in **both** independently materialized
views, with zero skips, import errors and fixture errors — and a different
passing subset does not substitute for it. The focused negatives in
`VERIFICATION.md` are part of the same obligation: refusals must be reachable,
distinct, and correctly staged, because a context that can only succeed proves
nothing about the view it claims to have built.
